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
# Test Mode Control Section
###############################################
def init_test_mode():
    """初始化測試模式狀態"""
    if "test_mode" not in st.session_state:
        st.session_state["test_mode"] = False

def toggle_test_mode():
    """切換測試模式"""
    st.session_state["test_mode"] = not st.session_state.get("test_mode", False)

def is_test_mode():
    """檢查是否為測試模式"""
    return st.session_state.get("test_mode", False)

def render_test_mode_controls():
    """渲染增強的測試模式控制項"""
    init_test_mode()
    
    # 使用容器和樣式創建突出的測試模式面板
    if is_test_mode():
        # 測試模式已啟用 - 橙色警告樣式
        st.markdown("""
        <div style="
            background: linear-gradient(90deg, #FF6B35, #F7931E);
            padding: 15px;
            border-radius: 10px;
            border-left: 5px solid #E55100;
            margin-bottom: 20px;
            color: white;
            font-weight: bold;
        ">
            🧪 <strong>測試模式已啟用</strong> - 所有操作都是模擬的，不會產生真實的外部請求或費用
        </div>
        """, unsafe_allow_html=True)
        
        # 測試模式控制面板
        with st.container():
            st.markdown("### 🧪 測試模式控制面板")
            
            # 分三列布局
            col1, col2, col3 = st.columns([2, 2, 2])
            
            with col1:
                if st.button("🔄 切換到正常模式", help="停用測試模式，使用真實 API 服務", type="secondary"):
                    toggle_test_mode()
                    st.rerun()
                    
                # 顯示測試統計
                if "dynamic_queue" in st.session_state:
                    dq = st.session_state["dynamic_queue"]
                    test_tasks = [t for t in dq["task_queue"] if t.get("test_type")]
                    test_results = [r for r in dq["results"] if r.get("test_mode")]
                    st.metric("測試任務", len(test_tasks))
                    st.metric("測試結果", len(test_results))
            
            with col2:
                st.markdown("**🎯 快速測試**")
                if st.button("� 添加科技類測試", help="添加科技主題的測試任務"):
                    from dynamic_queue_manager import DynamicQueueManager
                    test_url = f"https://www.youtube.com/watch?v=test_tech_{len(st.session_state.get('dynamic_queue', {}).get('task_queue', []))}"
                    ok, msg = DynamicQueueManager.add_url(test_url, test_type='tech')
                    if ok:
                        st.success("🧪 科技測試任務已添加")
                    else:
                        st.warning(f"添加失敗：{msg}")
                        
                if st.button("📰 添加新聞類測試", help="添加新聞主題的測試任務"):
                    from dynamic_queue_manager import DynamicQueueManager
                    test_url = f"https://www.youtube.com/watch?v=test_news_{len(st.session_state.get('dynamic_queue', {}).get('task_queue', []))}"
                    ok, msg = DynamicQueueManager.add_url(test_url, test_type='news')
                    if ok:
                        st.success("🧪 新聞測試任務已添加")
                    else:
                        st.warning(f"添加失敗：{msg}")
            
            with col3:
                st.markdown("**📊 測試選項**")
                
                # 錯誤模擬控制
                error_simulation = st.checkbox("🎲 啟用錯誤模擬", value=True, help="10% 機率模擬處理錯誤")
                if error_simulation:
                    st.session_state["test_error_simulation"] = True
                else:
                    st.session_state["test_error_simulation"] = False
                
                # 處理速度控制
                speed_mode = st.selectbox(
                    "⚡ 處理速度",
                    ["快速 (1-2秒)", "正常 (2-3秒)", "慢速 (3-5秒)"],
                    index=1,
                    help="調整測試任務的處理速度"
                )
                st.session_state["test_speed_mode"] = speed_mode
                
                # 清除測試數據
                if st.button("🗑️ 清除測試數據", help="清除所有測試任務和結果"):
                    if "dynamic_queue" in st.session_state:
                        dq = st.session_state["dynamic_queue"]
                        # 移除測試任務
                        dq["task_queue"] = [t for t in dq["task_queue"] if not t.get("test_type")]
                        # 移除測試結果
                        dq["results"] = [r for r in dq["results"] if not r.get("test_mode")]
                        # 移除測試錯誤記錄
                        dq["error_log"] = [e for e in dq["error_log"] if not e.get("test_mode")]
                        st.success("🧪 測試數據已清除")
                        st.rerun()
        
        # 測試模式說明 (可折疊)
        with st.expander("❓ 測試模式說明", expanded=False):
            st.markdown("""
            **🧪 測試模式功能：**
            - **完全隔離**：不會對外發送任何真實 API 請求
            - **快速響應**：2-3 秒內完成整個處理流程
            - **真實體驗**：結果格式與正常模式完全相同
            - **錯誤模擬**：可模擬各種錯誤情況進行測試
            - **資源節省**：不消耗任何 API 配額或費用
            
            **🎯 適用場景：**
            - 功能演示和展示
            - 開發階段的功能測試
            - 新功能驗證
            - 系統壓力測試
            - 離線環境測試
            
            **🔍 測試數據來源：**
            - 使用預設的 5 種測試樣本
            - 涵蓋科技、新聞、播客等不同主題
            - 自動輪換不同的測試內容
            """)
    else:
        # 正常模式 - 綠色信息樣式
        st.markdown("""
        <div style="
            background: linear-gradient(90deg, #4CAF50, #66BB6A);
            padding: 15px;
            border-radius: 10px;
            border-left: 5px solid #2E7D32;
            margin-bottom: 20px;
            color: white;
            font-weight: bold;
        ">
            ✅ <strong>正常模式</strong> - 使用真實的 API 服務進行處理
        </div>
        """, unsafe_allow_html=True)
        
        # 正常模式控制面板
        col1, col2 = st.columns([3, 1])
        
        with col1:
            st.info("💡 **提示**: 切換到測試模式可以安全地測試功能而不消耗 API 配額")
        
        with col2:
            if st.button("🧪 切換到測試模式", help="啟用測試模式，使用模擬數據", type="primary"):
                toggle_test_mode()
                st.rerun()

###############################################
# Dynamic Queue Experimental Section
###############################################
st.divider()

# 渲染測試模式控制項
render_test_mode_controls()

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
    
    # 測試按鈕 - 根據測試模式狀態調整行為
    if is_test_mode():
        test_pressed = st.button("🧪 加入測試任務", help="在測試模式下添加模擬任務")
    else:
        test_pressed = st.button("🧪 測試模式", help="請先切換到測試模式以使用此功能", disabled=True)

# 處理測試按鈕
if test_pressed and is_test_mode():
    if "dynamic_queue" not in st.session_state:
        init_dynamic_queue_state()
    
    # 生成測試任務，URL 根據測試類型變化
    test_types = ["tech", "news", "podcast"]
    test_type = test_types[len(st.session_state['dynamic_queue']['task_queue']) % len(test_types)]
    task_count = len(st.session_state['dynamic_queue']['task_queue'])
    
    # 使用新的 add_url 方法添加測試任務
    test_url = f"https://www.youtube.com/watch?v=test_{test_type}_{task_count}"
    ok, msg = DynamicQueueManager.add_url(test_url, test_type=test_type, sample_id=task_count)
    
    if ok:
        st.success(f"🧪 測試任務已加入: {msg}")
    else:
        st.warning(f"⚠️ 測試任務加入失敗: {msg}")
    st.rerun()

# 處理控制按鈕
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
            
            # 測試任務特殊標記和樣式
            test_marker = ""
            if t.get("test_type") or t.get("test_mode"):
                test_type = t.get("test_type", "general")
                test_marker = f"🧪 [測試-{test_type.upper()}] "
            
            step_info = f" - {t.get('step', '')}" if t.get('step') and status == "processing" else ""
            label = f"{prefix} {test_marker}[{status}{step_info}] {t['url']}"
            
            # 測試任務使用不同的展開樣式
            is_test_task = bool(t.get("test_type") or t.get("test_mode"))
            expanded = (status=="processing") or (is_test_task and status=="completed")
            
            with st.expander(label, expanded=expanded):
                # 添加測試任務的特殊樣式
                if is_test_task:
                    st.markdown("""
                    <div style="
                        background-color: #FFF3E0;
                        border: 2px dashed #FF9800;
                        border-radius: 8px;
                        padding: 10px;
                        margin-bottom: 10px;
                    ">
                        🧪 <strong>測試任務</strong> - 使用模擬數據處理
                    </div>
                    """, unsafe_allow_html=True)
                
                st.write(f"任務 ID: {t['id']}")
                if t.get("test_type"):
                    st.write(f"測試類型: {t['test_type']}")
                if t.get("sample_id") is not None:
                    st.write(f"樣本 ID: {t['sample_id']}")
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
            is_test_result = r.get('test_mode', False)
            
            # 測試結果使用特殊圖示和標記
            icon = "🧪" if is_test_result else "📄"
            test_label = " [測試結果]" if is_test_result else ""
            
            with st.expander(f"{icon} {title}{test_label}", expanded=False):
                # 測試結果的特殊樣式
                if is_test_result:
                    st.markdown("""
                    <div style="
                        background-color: #E8F5E8;
                        border: 2px solid #4CAF50;
                        border-radius: 8px;
                        padding: 10px;
                        margin-bottom: 10px;
                    ">
                        🧪 <strong>測試模式結果</strong> - 模擬數據生成
                    </div>
                    """, unsafe_allow_html=True)
                
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
