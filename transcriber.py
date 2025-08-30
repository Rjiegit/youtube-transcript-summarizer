import whisper
import os
from faster_whisper import WhisperModel
from logger import logger
import time
from typing import Optional

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


class Transcriber:
    def __init__(self, model_size="base"):
        self.model_size = model_size

    def transcribe(self, file_path):
        # 檢測測試模式
        if self._is_test_mode(file_path):
            logger.info(f"[測試模式] 模擬轉錄音訊檔案...")
            return self._mock_transcribe(file_path)
        else:
            return self.transcribe_with_faster_whisper(file_path)

    def transcribe_with_whisper(self, file_path):
        logger.info(f"Transcribing audio with Whisper...")
        whisper_model = whisper.load_model(self.model_size)
        result = whisper_model.transcribe(file_path, verbose=True, fp16=False)
        return result["text"]

    def transcribe_with_faster_whisper(self, file_path):
        logger.info(f"Transcribing audio with Faster Whisper...")
        whisper_model = WhisperModel(
            self.model_size,
            compute_type="int8",
        )
        segments, _ = whisper_model.transcribe(file_path)

        transcript_text = ""
        for segment in segments:
            # print(f"[{segment.start:.2f}s -> {segment.end:.2f}s] {segment.text}")
            transcript_text += segment.text
        return transcript_text

    def _is_test_mode(self, file_path: str = None) -> bool:
        """檢測是否為測試模式"""
        # 方法 1: 檢查 Streamlit session_state 中的測試模式標記
        if st and hasattr(st, "session_state"):
            try:
                if st.session_state.get("test_mode", False):
                    return True
            except Exception:
                pass

        # 方法 2: 檢查檔案路徑是否為測試檔案
        if file_path:
            filename = os.path.basename(file_path).lower()
            if "test" in filename or "mock" in filename:
                return True
            # 只有 mock_audio 開頭的 tmp 檔案才視為測試檔案
            if "/tmp/" in file_path and "mock_audio" in filename:
                return True

        return False

    def _mock_transcribe(self, file_path: str) -> str:
        """模擬轉錄過程，返回測試樣本文字"""
        if not TestSampleManager:
            raise ImportError("TestSampleManager not available for mock transcribe")

        # 模擬 1 秒的轉錄時間
        time.sleep(1.0)

        # 使用 TestSampleManager 獲取模擬轉錄結果
        manager = TestSampleManager()

        # 檢查是否需要模擬錯誤
        if manager.simulate_error(0.1):  # 10% 錯誤機率
            error_msg = manager.get_random_error_message()
            logger.error(f"[測試模式] 模擬轉錄錯誤: {error_msg}")
            raise Exception(f"[測試模式] {error_msg}")

        # 嘗試從檔案路徑提取任務 ID
        task_id = None
        filename = os.path.basename(file_path)
        if "test_" in filename:
            # 提取任務 ID 用於選擇對應樣本
            import re

            match = re.search(r"test_\w+", filename)
            if match:
                task_id = match.group()

        # 獲取模擬轉錄文字
        transcript = manager.get_mock_transcript(file_path, task_id)

        logger.info(f"[測試模式] 模擬轉錄完成，文字長度: {len(transcript)} 字元")
        logger.info(f"[測試模式] 轉錄來源: {filename}")

        return transcript
