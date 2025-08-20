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

col_in, col_btn, col_ctrl = st.columns([4,1,2])
with col_in:
    dq["current_url_input"] = st.text_input("輸入 YouTube URL 並加入隊列", value=dq.get("current_url_input", ""))
with col_btn:
    if st.button("➕ 加入隊列"):
        ok, msg = DynamicQueueManager.add_url(dq.get("current_url_input", ""))
        if ok:
            dq["current_url_input"] = ""
            st.success(msg)
        else:
            st.warning(msg)
        st.rerun()
with col_ctrl:
    start = st.button("▶️ 開始", disabled=dq["is_processing"])
    stop = st.button("⏹ 停止", disabled=not dq["is_processing"])
    clear = st.button("🧹 清空", disabled=dq["is_processing"])
    if start:
        DynamicQueueManager.start_processing()
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

update_stats()
stats = dq["stats"]
st.markdown(f"**進度**: {stats['completed']} / {stats['total']} 完成 | 失敗: {stats['failed']}")
if dq["is_processing"]:
    st.info("處理中... 新增的任務會自動排隊。")
elif stats['waiting'] > 0:
    st.info("有等待中的任務，按 ▶️ 開始 進行處理。")

with st.expander("📋 任務隊列", expanded=True):
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
                            st.warning(f"檔案不存在: {summary_path}")
                            # 嘗試尋找可能的替代路徑
                            if summary_path:
                                possible_paths = [
                                    f"data/{os.path.basename(summary_path)}",
                                    f"data/_summarized_{os.path.basename(summary_path)}",
                                    summary_path.replace("_summarized/", "data/")
                                ]
                                for alt_path in possible_paths:
                                    if os.path.exists(alt_path):
                                        st.info(f"找到替代檔案: {alt_path}")
                                        with open(alt_path, 'r', encoding='utf-8') as f:
                                            content = f.read()
                                        if len(content) > 2000:
                                            st.markdown(content[:2000] + "\n\n...(內容過長，已截斷)")
                                        else:
                                            st.markdown(content)
                                        break
                                else:
                                    st.error("找不到任何可能的檔案路徑")
                    except Exception as e:
                        st.error(f"讀取檔案失敗: {e}")
                
                with col2:
                    download_content = None
                    download_filename = None
                    
                    # 嘗試從多個可能的路徑讀取檔案
                    if summary_path:
                        possible_paths = [
                            summary_path,
                            f"data/{os.path.basename(summary_path)}",
                            f"data/_summarized_{os.path.basename(summary_path)}",
                            summary_path.replace("_summarized/", "data/")
                        ]
                        
                        for path in possible_paths:
                            if os.path.exists(path):
                                try:
                                    with open(path, 'r', encoding='utf-8') as f:
                                        download_content = f.read()
                                    download_filename = os.path.basename(path)
                                    break
                                except Exception:
                                    continue
                    
                    if download_content:
                        st.download_button(
                            "📥 下載",
                            data=download_content,
                            file_name=download_filename,
                            mime="text/markdown",
                            key=f"download_{r['id']}"
                        )
                    else:
                        st.error("無法找到檔案")

# 原單檔處理歷史紀錄
if st.session_state["history"]:
    st.subheader("本次瀏覽歷史紀錄")
    for i, record in enumerate(reversed(st.session_state["history"])):
        title = record.get("title") or record.get("url")
        with st.expander(f"{title}"):
            st.markdown(record["summary"])
