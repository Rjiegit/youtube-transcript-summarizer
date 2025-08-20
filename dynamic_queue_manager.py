"""Dynamic queue manager implementing add + processing loop using Streamlit session state."""
from __future__ import annotations
import streamlit as st
import uuid
from typing import Dict, Any, Optional
from queue_state import get_queue_state, update_stats, now_iso
from url_validator import normalize_youtube_url, is_valid_youtube_url
from youtube_downloader import YouTubeDownloader
from transcriber import Transcriber
from summarizer import Summarizer
from file_manager import FileManager
import os

# 可注入供測試使用的 provider 類
class _Providers:
    downloader_cls = YouTubeDownloader
    transcriber_cls = Transcriber
    summarizer_cls = Summarizer

def configure_providers(*, downloader=None, transcriber=None, summarizer=None):
    """Optional DI for testing."""
    if downloader:
        _Providers.downloader_cls = downloader
    if transcriber:
        _Providers.transcriber_cls = transcriber
    if summarizer:
        _Providers.summarizer_cls = summarizer

# NOTE: We reuse existing summarization pipeline components sequentially.

class DynamicQueueManager:
    @staticmethod
    def add_url(raw_url: str) -> tuple[bool, str]:
        dq = get_queue_state()
        if not raw_url.strip():
            return False, "URL 為空"
        if not is_valid_youtube_url(raw_url):
            return False, "不是有效的 YouTube URL"
        norm = normalize_youtube_url(raw_url)
        # 去重
        for t in dq["task_queue"]:
            if t.get("url") == norm:
                return False, "此 URL 已在隊列中"
        task_id = uuid.uuid4().hex[:12]
        dq["task_queue"].append({
            "id": task_id,
            "url": norm,
            "status": "waiting",
            "title": "",
            "added_time": now_iso(),
            "start_time": "",
            "end_time": "",
            "error_msg": "",
            "result_path": "",
            "retry_count": 0,
        })
        update_stats()
        return True, "已加入隊列"

    @staticmethod
    def start_processing():
        dq = get_queue_state()
        if dq["is_processing"]:
            return
        dq["is_processing"] = True
        dq["should_stop"] = False

    @staticmethod
    def stop_processing():
        dq = get_queue_state()
        dq["should_stop"] = True

    @staticmethod
    def clear_queue():
        dq = get_queue_state()
        dq["task_queue"].clear()
        dq["results"].clear()
        dq["error_log"].clear()
        dq["current_index"] = 0
        dq["is_processing"] = False
        dq["should_stop"] = False
        update_stats()

    @staticmethod
    def retry_task(task_id: str) -> bool:
        dq = get_queue_state()
        for t in dq["task_queue"]:
            if t["id"] == task_id and t["status"] == "failed":
                t["status"] = "waiting"
                t["error_msg"] = ""
                t["retry_count"] += 1
                update_stats()
                return True
        return False

    @staticmethod
    def processing_loop():
        dq = get_queue_state()
        if not dq["is_processing"]:
            return
        if dq["should_stop"]:
            dq["is_processing"] = False
            return
        # 邊界：走到隊列尾 -> 停止
        if dq["current_index"] >= len(dq["task_queue"]):
            dq["is_processing"] = False
            return
        
        task = dq["task_queue"][dq["current_index"]]
        
        # 跳過已完成或失敗的任務，自動前進到下一個
        if task["status"] in ("completed", "failed"):
            dq["current_index"] += 1
            update_stats()
            # 如果還有下一個任務，觸發rerun繼續處理
            if dq["current_index"] < len(dq["task_queue"]):
                st.rerun()
            else:
                dq["is_processing"] = False
            return
        
        # 處理等待中的任務
        if task["status"] == "waiting":
            task["status"] = "processing"
            task["start_time"] = now_iso()
            task["step"] = "downloading"
            try:
                downloader = _Providers.downloader_cls(task["url"])
                dl_result = downloader.download()
                file_path = dl_result["path"]
                task["step"] = "transcribing"
                transcriber = _Providers.transcriber_cls(model_size="tiny")
                transcription_text = transcriber.transcribe(file_path)
                task["step"] = "summarizing"
                summarizer = _Providers.summarizer_cls()
                file_title = os.path.splitext(os.path.basename(file_path))[0]
                # 使用時間戳記和任務ID確保檔名唯一性
                timestamp = now_iso().replace(":", "").replace("-", "").replace("T", "_")[:15]  # YYYYMMDD_HHMMSS
                unique_prefix = f"{timestamp}_{task['id'][:8]}"
                
                # 清理檔名並截斷過長的檔名
                sanitized_title = FileManager.sanitize_filename(file_title)
                # 計算可用的標題長度 (總長度 - prefix - 副檔名)
                max_title_length = 200 - len(unique_prefix) - 5  # 5 for ".md" + "_"
                if len(sanitized_title) > max_title_length:
                    sanitized_title = sanitized_title[:max_title_length]
                
                final_filename = f"{unique_prefix}_{sanitized_title}.md"
                
                summarized_text = summarizer.summarize(file_title, transcription_text)
                FileManager.save_text(summarized_text, output_file=final_filename)
                
                # 實際檔案路徑
                actual_file_path = f"data/{final_filename}"
                task["title"] = file_title
                task["status"] = "completed"
                task["step"] = "done"
                task["end_time"] = now_iso()
                task["result_path"] = actual_file_path
                dq["results"].append({
                    "id": task["id"],
                    "title": file_title,
                    "summary_path": actual_file_path,
                })
            except Exception as e:
                task["status"] = "failed"
                task["step"] = "error"
                task["end_time"] = now_iso()
                task["error_msg"] = str(e)
                dq["error_log"].append({
                    "id": task["id"],
                    "url": task["url"],
                    "error": str(e),
                    "time": now_iso(),
                })
            finally:
                update_stats()
                # 只在處理完成後觸發一次 rerun 來更新 UI
                st.rerun()

