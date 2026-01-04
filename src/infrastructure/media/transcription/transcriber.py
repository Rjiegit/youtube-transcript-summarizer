import os
from faster_whisper import WhisperModel
from src.core.logger import logger
import time
from typing import Optional

# Optional dependency for legacy whisper path.
try:
    import whisper
except ImportError:
    whisper = None

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
        if whisper is None:
            raise RuntimeError("whisper dependency missing. Install openai-whisper to use this path.")
        whisper_model = whisper.load_model(self.model_size)
        result = whisper_model.transcribe(file_path, verbose=True, fp16=False)
        return result["text"]

    def transcribe_with_faster_whisper(self, file_path):
        logger.info(f"Transcribing audio with Faster Whisper...")
        whisper_model = WhisperModel(
            self.model_size,
            compute_type="int8",
        )
        segments, info = whisper_model.transcribe(file_path)

        total_duration = self._get_total_duration_seconds(info)
        next_progress = 10
        last_segment_end = 0.0

        transcript_text = ""
        for segment in segments:
            # print(f"[{segment.start:.2f}s -> {segment.end:.2f}s] {segment.text}")
            transcript_text += segment.text

            if total_duration:
                updates, next_progress = self._get_progress_updates(
                    segment.end, total_duration, next_progress
                )
                for progress in updates:
                    logger.info(f"[進度] 轉錄 {progress}%")
            last_segment_end = segment.end

        if total_duration and last_segment_end >= total_duration:
            logger.info("[進度] 轉錄 100%")

        return transcript_text

    def _get_total_duration_seconds(self, info: Optional[object]) -> Optional[float]:
        if not info:
            return None

        duration = getattr(info, "duration", None)
        if isinstance(duration, (int, float)) and duration > 0:
            return float(duration)

        duration_ms = getattr(info, "duration_ms", None)
        if isinstance(duration_ms, (int, float)) and duration_ms > 0:
            return float(duration_ms) / 1000.0

        return None

    def _get_progress_updates(
        self, segment_end: float, total_duration: float, next_progress: int
    ) -> tuple[list[int], int]:
        if total_duration <= 0:
            return [], next_progress

        progress = int((segment_end / total_duration) * 100)
        updates = []
        while progress >= next_progress and next_progress <= 100:
            updates.append(next_progress)
            next_progress += 10
        return updates, next_progress

    def _is_test_mode(self, file_path: str = None) -> bool:
        """檢測是否為測試模式"""
        # 只接受顯式旗標（Streamlit 開關或環境變數），避免因檔名含關鍵字誤觸
        if st and hasattr(st, "session_state"):
            try:
                if st.session_state.get("test_mode", False):
                    return True
            except Exception:
                pass

        env_flag = os.getenv("APP_ENV", "").lower() == "test"
        force_flag = os.getenv("FORCE_TEST_MODE", "").lower() in [
            "1",
            "true",
            "yes",
            "on",
        ]
        return env_flag or force_flag

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
