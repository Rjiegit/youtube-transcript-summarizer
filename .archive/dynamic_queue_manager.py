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
from summary_storage import SummaryStorage
import os
import time
import random

try:
    from test_sample_manager import TestSampleManager
except ImportError:
    TestSampleManager = None

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
    def _is_test_task(task: Dict[str, Any]) -> bool:
        """檢測是否為測試任務"""
        # 方法 1: 檢查 Streamlit session_state
        if hasattr(st, 'session_state') and st.session_state.get('test_mode', False):
            return True
        
        # 方法 2: 檢查任務的 test_type 標記
        if task.get('test_type'):
            return True
        
        # 方法 3: 檢查 URL 中的測試標記
        url = task.get('url', '')
        if url and any(marker in url for marker in ['test_', 'test/', 'v=test']):
            return True
        
        # 方法 4: 檢查任務ID中的測試標記
        task_id = task.get('id', '')
        if task_id and any(marker in task_id for marker in ['test_', 'mock_']):
            return True
            
        return False
    
    @staticmethod
    def _process_test_task(task: Dict[str, Any]):
        """處理測試任務的完整流程"""
        dq = get_queue_state()
        
        try:
            # 模擬下載階段
            task["step"] = "downloading"
            st.rerun()  # 更新 UI 顯示當前步驟
            
            time.sleep(random.uniform(0.5, 1.2))  # 模擬下載時間
            
            downloader = _Providers.downloader_cls(task["url"])
            dl_result = downloader.download()
            file_path = dl_result["path"]
            file_title = dl_result["title"]
            
            # 模擬轉錄階段
            task["step"] = "transcribing"
            st.rerun()
            
            time.sleep(random.uniform(0.8, 1.5))  # 模擬轉錄時間
            
            transcriber = _Providers.transcriber_cls(model_size="tiny")
            transcription_text = transcriber.transcribe(file_path)
            
            # 模擬摘要階段
            task["step"] = "summarizing"
            st.rerun()
            
            time.sleep(random.uniform(0.8, 1.2))  # 模擬摘要時間
            
            summarizer = _Providers.summarizer_cls()
            # 在轉錄文字中添加測試標記以觸發測試模式
            test_transcript = transcription_text + ' [測試模式]'
            summarized_text = summarizer.summarize(file_title, test_transcript)
            
            # 模擬存儲階段
            task["step"] = "saving"
            st.rerun()
            
            time.sleep(random.uniform(0.3, 0.6))  # 模擬存儲時間
            
            # 測試模式下的檔案名處理
            timestamp = now_iso().replace(":", "").replace("-", "").replace("T", "_")[:15]
            unique_prefix = f"[TEST]_{timestamp}_{task['id'][:8]}"
            
            sanitized_title = FileManager.sanitize_filename(file_title)
            max_title_length = 200 - len(unique_prefix) - 5
            if len(sanitized_title) > max_title_length:
                sanitized_title = sanitized_title[:max_title_length]
            
            final_filename = f"{unique_prefix}_{sanitized_title}.md"
            
            # 使用測試模式存儲檔案（添加測試標記）
            test_summary = summarized_text + '\n\n[測試模式]'
            file_result = FileManager.save_text(test_summary, output_file=final_filename)
            
            # 模擬 Notion 存儲（可選）
            try:
                storage = SummaryStorage()
                storage_result = storage.save(file_title, test_summary, 'gemini-2.0-flash', task["url"])
                notion_page_id = storage_result.get('page_id', 'mock_page_test')
            except Exception:
                notion_page_id = 'mock_page_test_fallback'
            
            # 成功完成
            task["title"] = file_title
            task["status"] = "completed"
            task["step"] = "done"
            task["end_time"] = now_iso()
            task["result_path"] = file_result.get('path', f'mock_data/{final_filename}')
            task["test_mode"] = True  # 標記為測試任務
            
            dq["results"].append({
                "id": task["id"],
                "title": file_title,
                "summary_path": task["result_path"],
                "test_mode": True,
                "notion_page_id": notion_page_id
            })
            
            # 記錄測試成功日誌
            from logger import logger
            logger.info(f"[測試模式] 任務完成: {task['id']} - {file_title}")
            logger.info(f"[測試模式] 檔案路徑: {task['result_path']}")
            logger.info(f"[測試模式] Notion 頁面: {notion_page_id}")
            
        except Exception as e:
            # 記錄測試錯誤日誌
            from logger import logger
            logger.error(f"[測試模式] 任務失敗: {task['id']} - {str(e)}")
            
            task["status"] = "failed"
            task["step"] = "error"
            task["end_time"] = now_iso()
            task["error_msg"] = f"[測試模式] {str(e)}"
            task["test_mode"] = True
            
            dq["error_log"].append({
                "id": task["id"],
                "url": task["url"],
                "error": task["error_msg"],
                "time": now_iso(),
                "test_mode": True
            })
    
    @staticmethod
    def _process_test_task_simple(task: Dict[str, Any]):
        """處理測試任務的簡化流程（適應當前架構）"""
        dq = get_queue_state()
        
        try:
            task["status"] = "processing"
            task["start_time"] = now_iso()
            
            # 模擬下載階段 (進一步優化)
            task["step"] = "downloading"
            time.sleep(random.uniform(0.05, 0.15))  # 進一步縮短下載時間
            
            downloader = _Providers.downloader_cls(task["url"])
            dl_result = downloader.download()
            file_path = dl_result["path"]
            file_title = dl_result["title"]
            
            # 模擬轉錄階段 (進一步優化)
            task["step"] = "transcribing"
            time.sleep(random.uniform(0.1, 0.2))  # 進一步縮短轉錄時間
            
            transcriber = _Providers.transcriber_cls(model_size="tiny")
            transcription_text = transcriber.transcribe(file_path)
            
            # 模擬摘要階段 (進一步優化)
            task["step"] = "summarizing"
            time.sleep(random.uniform(0.1, 0.3))  # 進一步縮短摘要時間
            
            summarizer = _Providers.summarizer_cls()
            # 在轉錄文字中添加測試標記以觸發測試模式
            test_transcript = transcription_text + ' [測試模式]'
            summarized_text = summarizer.summarize(file_title, test_transcript)
            
            # 模擬存儲階段 (進一步優化)
            task["step"] = "saving"
            time.sleep(random.uniform(0.05, 0.1))  # 進一步縮短存儲時間
            
            # 測試模式下的檔案名處理
            timestamp = now_iso().replace(":", "").replace("-", "").replace("T", "_")[:15]
            unique_prefix = f"[TEST]_{timestamp}_{task['id'][:8]}"
            
            sanitized_title = FileManager.sanitize_filename(file_title)
            max_title_length = 200 - len(unique_prefix) - 5
            if len(sanitized_title) > max_title_length:
                sanitized_title = sanitized_title[:max_title_length]
            
            final_filename = f"{unique_prefix}_{sanitized_title}.md"
            
            # 使用測試模式存儲檔案（添加測試標記）
            test_summary = summarized_text + '\n\n[測試模式]'
            FileManager.save_text(test_summary, output_file=final_filename)
            
            # 實際檔案路徑
            actual_file_path = f"data/{final_filename}"
            task["title"] = file_title
            task["status"] = "completed"
            task["step"] = "done"
            task["end_time"] = now_iso()
            task["result_path"] = actual_file_path
            task["test_mode"] = True  # 標記為測試任務
            
            dq["results"].append({
                "id": task["id"],
                "title": file_title,
                "summary_path": actual_file_path,
                "test_mode": True
            })
            
            # 記錄測試成功日誌
            from logger import logger
            logger.info(f"[測試模式] 任務完成: {task['id']} - {file_title}")
            logger.info(f"[測試模式] 檔案路徑: {actual_file_path}")
            
        except Exception as e:
            # 記錄測試錯誤日誌
            from logger import logger
            logger.error(f"[測試模式] 任務失敗: {task['id']} - {str(e)}")
            
            task["status"] = "failed"
            task["step"] = "error"
            task["end_time"] = now_iso()
            task["error_msg"] = f"[測試模式] {str(e)}"
            task["test_mode"] = True
            
            dq["error_log"].append({
                "id": task["id"],
                "url": task["url"],
                "error": task["error_msg"],
                "time": now_iso(),
                "test_mode": True
            })
        
        finally:
            update_stats()
            st.rerun()

    @staticmethod
    def auto_start_if_needed():
        """檢查是否需要自動開始處理"""
        dq = get_queue_state()
        if not dq["is_processing"] and dq["task_queue"]:
            # 檢查是否有等待中的任務
            waiting_tasks = [t for t in dq["task_queue"] if t["status"] == "waiting"]
            if waiting_tasks:
                dq["is_processing"] = True
                dq["should_stop"] = False
                return True
        return False
    
    @staticmethod
    def add_url(raw_url: str, test_type: Optional[str] = None, sample_id: Optional[int] = None) -> tuple[bool, str]:
        """新增任務到佇列。支援測試任務標記。"""
        # 直接操作 session state 而不是通過引用
        if "dynamic_queue" not in st.session_state:
            from queue_state import init_dynamic_queue_state
            init_dynamic_queue_state()
        
        dq = st.session_state["dynamic_queue"]
        
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
        
        # 如果是測試任務，添加測試標記到 ID 中
        if test_type:
            task_id = f"test_{task_id}"
        
        # 建立新任務
        new_task = {
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
            "test_type": test_type,      # 添加測試類型標記
            "sample_id": sample_id,      # 添加測試樣本 ID
        }
        
        # 直接加入到 session state
        dq["task_queue"].append(new_task)
        update_stats()
        
        # 記錄日誌
        from logger import logger
        if test_type:
            logger.info(f"[測試模式] 新增測試任務: {task_id} - {norm} (類型: {test_type})")
            return True, f"已加入測試隊列 (類型: {test_type})"
        else:
            logger.info(f"新增任務: {task_id} - {norm}")
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
        """執行動態任務處理迴圈。自動識別測試任務使用 mock 處理流程。"""
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
            # 檢查是否為測試任務
            if DynamicQueueManager._is_test_task(task):
                # 處理測試任務
                from logger import logger
                logger.info(f"[測試模式] 開始處理測試任務: {task['id']}")
                DynamicQueueManager._process_test_task_simple(task)
            else:
                # 處理真實任務（原本的邏輯）
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
                    task["test_mode"] = False  # 標記為真實任務
                    dq["results"].append({
                        "id": task["id"],
                        "title": file_title,
                        "summary_path": actual_file_path,
                        "test_mode": False
                    })
                except Exception as e:
                    task["status"] = "failed"
                    task["step"] = "error"
                    task["end_time"] = now_iso()
                    task["error_msg"] = str(e)
                    task["test_mode"] = False
                    dq["error_log"].append({
                        "id": task["id"],
                        "url": task["url"],
                        "error": str(e),
                        "time": now_iso(),
                        "test_mode": False
                    })
                finally:
                    update_stats()
                    # 只在處理完成後觸發一次 rerun 來更新 UI
                    st.rerun()

