import streamlit as st
from transcriber import Transcriber
from summarizer import Summarizer
from summary_storage import SummaryStorage
from file_manager import FileManager
import os
import datetime
import pytz
from youtube_downloader import YouTubeDownloader

# Dynamic queue imports
from queue_state import init_dynamic_queue_state, get_queue_state, update_stats
from dynamic_queue_manager import DynamicQueueManager
from url_validator import is_valid_youtube_url

st.set_page_config(page_title="Whisper 分析工具", layout="wide")
st.title("Whisper 分析工具 - 影片/音訊自動摘要")

st.markdown("""
這個工具可以讓你輸入影片或音訊的網址，並自動下載、轉錄、摘要，並顯示結果。

**新功能 (實驗)**: 下方提供「動態隊列模式」，可連續添加多個 YouTube URL，自動依序處理。
""")

url = st.text_input("請輸入影片或音訊網址 (如 YouTube)")

# 初始化 session state 的歷史紀錄
if "history" not in st.session_state:
    st.session_state["history"] = []

if st.button("開始分析") and url:
    import time
    start_time = time.time()
    progress = st.progress(0, text="準備開始下載...")
    with st.spinner("正在處理，請稍候..."):
        # 下載影片/音訊
        try:
            progress.progress(10, text="開始下載影片/音訊...")
            downloader = YouTubeDownloader(url)
            result = downloader.download()
            file_path = result["path"]
            progress.progress(40, text=f"已下載: {file_path}\n開始語音轉錄...")
            st.success(f"已下載: {file_path}")
        except Exception as e:
            st.error(f"下載失敗: {e}")
            file_path = None
            progress.progress(0, text="下載失敗")
        
        if file_path:
            try:
                transcriber = Transcriber(model_size="tiny")
                progress.progress(60, text="語音轉錄中...")
                summarizer = Summarizer()
                summary_storage = SummaryStorage()
                file_title = os.path.splitext(os.path.basename(file_path))[0]
                transcription_text = transcriber.transcribe(file_path)
                progress.progress(80, text="轉錄完成，開始摘要...")
                datetime_now = datetime.datetime.now(pytz.timezone("Asia/Taipei")).strftime('%Y%m%d%H%M%S')
                summarized_text = summarizer.summarize(file_title, transcription_text)
                output_file = f"_summarized/{datetime_now}_{file_title}.md"
                FileManager.save_text(summarized_text, output_file=output_file)
                summary_storage.save(
                    title=file_title,
                    text=summarized_text,
                    model="",
                    url=file_path
                )
                progress.progress(100, text="摘要完成！")
                end_time = time.time()
                elapsed = end_time - start_time
                st.info(f"總處理時間：{elapsed:.1f} 秒")
                st.subheader("摘要結果")
                st.markdown(summarized_text)
                st.download_button("下載摘要檔案", data=summarized_text, file_name=os.path.basename(output_file))
                # 新增到 session_state 歷史紀錄
                st.session_state["history"].append({
                    "url": url,
                    "title": file_title,
                    "summary": summarized_text
                })
            except Exception as e:
                st.error(f"分析失敗: {e}")
                progress.progress(0, text="分析失敗")

###############################################
# Dynamic Queue Experimental Section
###############################################
st.divider()
st.header("🔄 動態隊列模式 (實驗)")

init_dynamic_queue_state()
dq = get_queue_state()

col_in, col_btn, col_ctrl = st.columns([5,1,2])
with col_in:
    dq["current_url_input"] = st.text_input("輸入 YouTube URL（加入後自動開始處理）", value=dq.get("current_url_input", ""))
with col_btn:
    add_pressed = st.button("➕ 加入並處理")
    
# 處理按鈕事件（在按鈕定義後）
if add_pressed:
    current_input = dq.get("current_url_input", "")
    if current_input.strip():
        # 確保 session state 存在
        if "dynamic_queue" not in st.session_state:
            init_dynamic_queue_state()
        
        # 調用 add_url
        ok, msg = DynamicQueueManager.add_url(current_input)
        
        if ok:
            # 直接更新 session state
            st.session_state["dynamic_queue"]["current_url_input"] = ""
            current_length = len(st.session_state["dynamic_queue"]["task_queue"])
            st.success(f"{msg}，隊列長度: {current_length}")
            # 立即重新渲染
            st.rerun()
        else:
            st.warning(msg)
    else:
        st.warning("請輸入 YouTube URL")
with col_ctrl:
    stop = st.button("⏹ 停止處理", disabled=not dq["is_processing"])
    clear = st.button("🧹 清空隊列", disabled=dq["is_processing"])
    
    # 測試按鈕 - 添加假任務來測試
    test_pressed = st.button("🧪 測試加入")

# 處理測試按鈕
if test_pressed:
    if "dynamic_queue" not in st.session_state:
        init_dynamic_queue_state()
    test_task = {
        "id": f"test_{len(st.session_state['dynamic_queue']['task_queue'])}",
        "url": f"https://www.youtube.com/watch?v=test{len(st.session_state['dynamic_queue']['task_queue'])}",
        "status": "waiting",
        "title": "測試任務",
        "added_time": "2025-08-20T12:00:00",
        "start_time": "",
        "end_time": "",
        "error_msg": "",
        "result_path": "",
        "retry_count": 0,
    }
    st.session_state["dynamic_queue"]["task_queue"].append(test_task)
    st.success(f"測試任務已加入，當前隊列長度: {len(st.session_state['dynamic_queue']['task_queue'])}")
    st.rerun()
    
    if stop:
        DynamicQueueManager.stop_processing()
        st.rerun()
    if clear:
        DynamicQueueManager.clear_queue()
        st.rerun()

# Trigger processing loop only if actually processing
if dq["is_processing"]:
    DynamicQueueManager.processing_loop()

# 重新獲取最新狀態用於顯示
dq = get_queue_state()
update_stats()
stats = dq["stats"]
st.markdown(f"**進度**: {stats['completed']} / {stats['total']} 完成 | 失敗: {stats['failed']}")
if dq["is_processing"]:
    st.info("🔄 處理中... 新增的任務會自動加入隊列並依序處理。")
elif stats['waiting'] > 0:
    st.info("⚠️ 有等待中的任務但處理已停止。加入新任務將自動重新開始處理。")
elif stats['total'] == 0:
    st.info("💡 輸入 YouTube URL 並點擊「加入並處理」開始使用動態隊列功能！")

with st.expander("📋 任務隊列", expanded=True):
    # 再次確保使用最新狀態
    dq = get_queue_state()
    # 除錯信息
    st.write(f"隊列狀態: 總數 {len(dq['task_queue'])}, 當前索引 {dq.get('current_index', 0)}, 處理中: {dq.get('is_processing', False)}")
    
    # 顯示原始 session state 內容（除錯用）
    if st.checkbox("顯示詳細除錯信息"):
        st.json(st.session_state.get("dynamic_queue", {}))
    
    if not dq["task_queue"]:
        st.write("目前沒有任務。")
    else:
        for idx, t in enumerate(dq["task_queue"]):
            status = t["status"]
            prefix = ""
            if status == "waiting":
                prefix = "🟡"
            elif status == "processing":
                prefix = "🟢"
            elif status == "completed":
                prefix = "✅"
            elif status == "failed":
                prefix = "❌"
            step_info = f" - {t.get('step', '')}" if t.get('step') and status == "processing" else ""
            label = f"{prefix} [{status}{step_info}] {t['url']}"
            with st.expander(label, expanded=(status=="processing")):
                st.write(f"任務 ID: {t['id']}")
                if t.get("step"):
                    st.write(f"當前步驟: {t['step']}")
                if t.get("title"):
                    st.write(f"標題: {t['title']}")
                if status == "failed":
                    st.error(t.get("error_msg") or "未知錯誤")
                    if st.button(f"重試 {t['id']}", key=f"retry-{t['id']}"):
                        if DynamicQueueManager.retry_task(t['id']):
                            st.rerun()
                if status == "completed" and t.get("result_path"):
                    # Show a link or small preview placeholder
                    st.success(f"已完成，檔案: {t['result_path']}")

with st.expander("❌ 錯誤記錄"):
    if not dq["error_log"]:
        st.write("無錯誤。")
    else:
        for e in dq["error_log"][-20:]:
            st.write(f"{e['time']} | {e['url']} | {e['error']}")

with st.expander("✅ 結果列表", expanded=True):
    if not dq["results"]:
        st.write("尚無結果。")
    else:
        for r in dq["results"][-20:]:
            title = r.get('title', r['id'])
            summary_path = r.get('summary_path', '')
            
            with st.expander(f"📄 {title}", expanded=False):
                col1, col2 = st.columns([3, 1])
                with col1:
                    st.write(f"**檔案路徑**: {summary_path}")
                    # 嘗試讀取並顯示摘要內容
                    try:
                        if summary_path and os.path.exists(summary_path):
                            with open(summary_path, 'r', encoding='utf-8') as f:
                                content = f.read()
                            st.markdown("**摘要內容**:")
                            # 限制顯示長度，避免頁面過長
                            if len(content) > 2000:
                                st.markdown(content[:2000] + "\n\n...(內容過長，已截斷)")
                            else:
                                st.markdown(content)
                        else:
                            st.error(f"檔案不存在: {summary_path}")
                    except Exception as e:
                        st.error(f"讀取檔案失敗: {e}")
                
                with col2:
                    if summary_path and os.path.exists(summary_path):
                        try:
                            with open(summary_path, 'r', encoding='utf-8') as f:
                                download_content = f.read()
                            st.download_button(
                                "📥 下載",
                                data=download_content,
                                file_name=os.path.basename(summary_path),
                                mime="text/markdown",
                                key=f"download_{r['id']}"
                            )
                        except Exception as e:
                            st.error(f"準備下載失敗: {e}")
                    else:
                        st.error("檔案不存在，無法下載")

# 原單檔處理歷史紀錄
if st.session_state["history"]:
    st.subheader("本次瀏覽歷史紀錄")
    for i, record in enumerate(reversed(st.session_state["history"])):
        title = record.get("title") or record.get("url")
        with st.expander(f"{title}"):
            st.markdown(record["summary"])

# 在頁面最後檢查是否需要自動開始處理（不會中斷UI顯示）
if not dq["is_processing"]:
    if DynamicQueueManager.auto_start_if_needed():
        st.rerun()
