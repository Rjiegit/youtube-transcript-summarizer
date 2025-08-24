from pytubefix import YouTube
from pytubefix.cli import on_progress
import os
from logger import logger
import subprocess
import time
from typing import Dict, Any

# 導入測試樣本管理器
try:
    from test_sample_manager import TestSampleManager
except ImportError:
    TestSampleManager = None

# 導入 Streamlit（如果可用）用於檢測測試模式
try:
    import streamlit as st
except ImportError:
    st = None

class YouTubeDownloader:
    def __init__(self, url, output_path="data"):
        self.url = url
        self.output_path = output_path
    
    def download(self):
        # 檢測測試模式
        if self._is_test_mode():
            logger.info(f"[測試模式] 模擬下載 YouTube 影片...")
            return self._mock_download()
        else:
            # Always use yt-dlp for download
            logger.info(f"Download YouTube video using yt-dlp...")
            return self._download_with_yt_dlp()

    def _download_with_yt_dlp(self):
        output_dir = os.path.join(self.output_path, "videos")
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
        cmd = [
            "yt-dlp",
            "-S", "res:360",
            "-o", os.path.join(output_dir, '%(title)s.%(ext)s'),
            self.url
        ]
        subprocess.run(cmd, check=True)
        # Find the latest downloaded video file (any extension)
        files = [f for f in os.listdir(output_dir) if os.path.isfile(os.path.join(output_dir, f))]
        if not files:
            raise Exception("yt-dlp did not download any video file.")
        latest_file = max([os.path.join(output_dir, f) for f in files], key=os.path.getctime)
        title = os.path.splitext(os.path.basename(latest_file))[0]
        return {"path": latest_file, "title": title}

    def _download_with_pytube(self):
        yt = YouTube(self.url, on_progress_callback=on_progress)
        video = yt.streams.filter(only_audio=True).first()
        if not os.path.exists(self.output_path):
            os.makedirs(self.output_path)
        video_path = video.download(output_path=self.output_path)
        logger.info(f"Downloaded file path: {video_path}, title: {yt.title}")
        return {"path": video_path, "title": yt.title}
    
    def _is_test_mode(self) -> bool:
        """檢測是否為測試模式"""
        # 方法 1: 檢查 Streamlit session_state 中的測試模式標記
        if st and hasattr(st, 'session_state'):
            try:
                if st.session_state.get("test_mode", False):
                    return True
            except Exception:
                pass
        
        # 方法 2: 檢查 URL 是否為測試 URL 模式
        if "test_" in self.url or "test/" in self.url or "v=test" in self.url:
            return True
        
        return False
    
    def _mock_download(self) -> Dict[str, Any]:
        """模擬下載過程，返回測試樣本資料"""
        if not TestSampleManager:
            raise ImportError("TestSampleManager not available for mock download")
        
        # 模擬 1-2 秒的下載時間
        import random
        download_time = random.uniform(1.0, 2.0)
        time.sleep(download_time)
        
        # 使用 TestSampleManager 獲取模擬結果
        manager = TestSampleManager()
        
        # 檢查是否需要模擬錯誤
        if manager.simulate_error(0.1):  # 10% 錯誤機率
            error_msg = manager.get_random_error_message()
            logger.error(f"[測試模式] 模擬錯誤: {error_msg}")
            raise Exception(f"[測試模式] {error_msg}")
        
        # 獲取模擬下載結果
        file_path, metadata = manager.get_mock_download_result(self.url)
        
        logger.info(f"[測試模式] 模擬下載完成: {metadata['title']}")
        logger.info(f"[測試模式] 檔案路徑: {file_path}")
        logger.info(f"[測試模式] 檔案大小: {metadata['file_size'] / 1024 / 1024:.1f} MB")
        
        return {
            "path": file_path, 
            "title": metadata['title'],
            "metadata": metadata  # 額外的元資料供後續使用
        }