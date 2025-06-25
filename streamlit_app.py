import streamlit as st
import os
import time
from datetime import datetime
from config import Config
from transcriber import Transcriber
from summarizer import Summarizer
from file_manager import FileManager
from summary_storage import SummaryStorage
from youtube_downloader import YouTubeDownloader
from logger import logger

st.set_page_config(page_title="Whisper 分析工具", layout="wide")
st.title("Whisper 分析工具 - 影片/音訊自動摘要")

st.markdown("""
這個工具可以讓你輸入影片或音訊的網址，並自動下載、轉錄、摘要，並顯示結果。
""")

url = st.text_input("請輸入影片或音訊網址 (如 YouTube)")

# 初始化 session state 的歷史紀錄
if "history" not in st.session_state:
    st.session_state["history"] = []

if st.button("開始分析") and url:
    start_time = time.time()
    progress = st.progress(0, text="準備開始下載...")
    with st.spinner("正在處理，請稍候..."):
        # Initialize configuration and components
        config = Config()

        # Initialize file_path to None
        file_path = None

        # Validate configuration
        config_valid = True
        try:
            config.validate()
        except ValueError as e:
            st.error(f"配置錯誤: {e}")
            progress.progress(0, text="配置錯誤")
            config_valid = False

        # Only proceed if configuration is valid
        if config_valid:
            # Initialize components with dependency injection
            transcriber = Transcriber(config=config)
            summarizer = Summarizer(config=config)
            file_manager = FileManager(config=config)
            summary_storage = SummaryStorage(config=config)

            # 下載影片/音訊
            try:
                progress.progress(10, text="開始下載影片/音訊...")
                downloader = YouTubeDownloader(url, output_path=config.data_dir)
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
                    # Process the file
                    progress.progress(60, text="語音轉錄中...")
                    # Extract the title from the file path
                    file_title = os.path.splitext(os.path.basename(file_path))[0]

                    # Transcribe the file
                    transcription_text = transcriber.transcribe(file_path)
                    progress.progress(80, text="轉錄完成，開始摘要...")

                    # Summarize the transcription
                    summarized_text = summarizer.summarize(file_title, transcription_text)

                    # Generate timestamp for the output file
                    datetime_now = datetime.now(config.timezone).strftime('%Y%m%d%H%M%S')
                    output_file = f"_summarized/{datetime_now}_{file_title}.md"

                    # Save the summary to a file
                    file_manager.save_text(summarized_text, output_file)

                    # Save the summary to storage (e.g., Notion)
                    summary_storage.save(
                        title=file_title,
                        text=summarized_text,
                        model="",
                        url=file_path
                    )

                    # Don't delete the original file in the Streamlit app
                    # to allow users to download it if needed

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
                    logger.error(f"分析失敗: {e}")
                    st.error(f"分析失敗: {e}")
                    progress.progress(0, text="分析失敗")

# 顯示本 session 歷史紀錄
if st.session_state["history"]:
    st.subheader("本次瀏覽歷史紀錄")
    for i, record in enumerate(reversed(st.session_state["history"])):
        # 以標題為主顯示
        title = record.get("title") or record.get("url")
        with st.expander(f"{title}"):
            st.markdown(record["summary"])
