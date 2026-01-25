import os
from openai import OpenAI
import requests
from dotenv import load_dotenv
import google.generativeai as genai
from src.core import prompt
from src.core.logger import logger
from src.infrastructure.llm.model_options import (
    GEMINI_MODEL,
    GEMINI_WEIGHTED_MODELS,
    OLLAMA_MODEL,
    OPENAI_MODEL,
)
import time
import random

from src.infrastructure.llm.gemini_model_selection import choose_weighted_model

try:
    import streamlit as st
except ImportError:
    st = None

try:
    from test_sample_manager import TestSampleManager
except ImportError:
    TestSampleManager = None

load_dotenv()


class Summarizer:
    def __init__(self):
        self.openai_api_key = os.getenv("OPENAI_API_KEY")
        self.google_gemini_api_key = os.getenv("GOOGLE_GEMINI_API_KEY")
        # Keep last-used backend/model label for callers
        self.last_backend = None  # one of: mock, gemini, openai, ollama, unknown
        self.last_model_label = None

    def summarize(self, title, text):
        # Decide backend based on environment and test mode
        backend = self._determine_backend(text)
        self.last_backend = backend

        if backend == "mock":
            self.last_model_label = self._get_model_label(backend)
            return self._mock_summarize(title, text)
        if backend == "gemini":
            selected_model = self._choose_gemini_model()
            self.last_model_label = selected_model
            return self.summarize_with_google_gemini(title, text, model=selected_model)
        if backend == "openai":
            self.last_model_label = self._get_model_label(backend)
            return self.summarize_with_openai(title, text)
        # Could add ollama auto-detect here in the future
        raise ValueError("No available summarization backend (set API keys or enable test mode)")

    def _determine_backend(self, text):
        if self._is_test_mode(text):
            return "mock"
        if self.google_gemini_api_key:
            return "gemini"
        if self.openai_api_key:
            return "openai"
        return "unknown"

    def _get_model_label(self, backend):
        if backend == "mock":
            return "mock"
        if backend == "gemini":
            return GEMINI_MODEL
        if backend == "openai":
            return OPENAI_MODEL
        if backend == "ollama":
            return OLLAMA_MODEL
        return "unknown"

    def _choose_gemini_model(self) -> str:
        selected_model = GEMINI_MODEL
        if GEMINI_WEIGHTED_MODELS:
            try:
                selected_model = choose_weighted_model(GEMINI_WEIGHTED_MODELS, rng=random)
            except ValueError:
                selected_model = GEMINI_MODEL
        logger.info(f"[Gemini] Selected model: {selected_model}")
        return selected_model

    def _is_test_mode(self, text):
        """檢測是否為測試模式"""
        # 只接受顯式旗標（Streamlit 開關或環境變數），避免因關鍵字誤觸
        if (
            st
            and hasattr(st, "session_state")
            and st.session_state.get("test_mode", False)
        ):
            return True

        env_flag = os.getenv("APP_ENV", "").lower() == "test"
        force_flag = os.getenv("FORCE_TEST_MODE", "").lower() in [
            "1",
            "true",
            "yes",
            "on",
        ]
        return env_flag or force_flag

    def _mock_summarize(self, title, text):
        """模擬摘要過程"""
        logger.info("[測試模式] 模擬文字摘要...")

        # 檢查 TestSampleManager 是否可用
        if TestSampleManager is None:
            logger.warning("[測試模式] TestSampleManager 不可用，使用基本模擬")
            time.sleep(random.uniform(0.8, 1.5))
            return f"[測試模式摘要] {title}\n\n這是一個模擬的摘要內容，用於測試目的。"

        # 模擬處理時間
        time.sleep(random.uniform(0.8, 1.5))

        # 檢查是否要模擬錯誤
        sample_manager = TestSampleManager()
        if sample_manager.simulate_error():
            error_msg = sample_manager.get_random_error_message()
            logger.error(f"[測試模式] 模擬摘要錯誤: {error_msg}")
            raise Exception(f"[測試模式] {error_msg}")

        # 根據標題或轉錄文字內容選擇對應樣本摘要
        summary = sample_manager.get_mock_summary(title, text)

        logger.info(f"[測試模式] 模擬摘要完成，摘要長度: {len(summary)} 字元")
        logger.info(f"[測試模式] 摘要來源: {title}")

        return summary

    def get_prompt(self, title, text):
        return prompt.PROMPT_3.format(title=title, text=text)

    def summarize_with_openai(self, title, text):
        if not self.openai_api_key:
            raise ValueError("API key is not set. Please add it to the .env file.")

        client = OpenAI(api_key=self.openai_api_key)
        prompt_text = self.get_prompt(title=title, text=text)
        resp = client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": prompt_text},
            ],
            temperature=0.5,
        )
        return resp.choices[0].message.content.strip()

    def summarize_with_google_gemini(self, title, text, model: str | None = None):
        if not self.google_gemini_api_key:
            raise ValueError("API key is not set. Please add it to the .env file.")

        genai.configure(api_key=self.google_gemini_api_key)

        selected_model = model or self._choose_gemini_model()
        self.last_model_label = selected_model
        gemini = genai.GenerativeModel(selected_model)
        response = gemini.generate_content(self.get_prompt(title=title, text=text))

        return response.text

    def summarize_with_ollama(self, title, text):
        logger.info(f"Summarize with Ollama...")
        url = "http://host.docker.internal:11434/api/generate"
        headers = {"Content-Type": "application/json"}
        data = {
            "model": OLLAMA_MODEL,
            "prompt": self.get_prompt(title=title, text=text),
            "stream": False,
        }
        response = requests.post(url, headers=headers, json=data)
        if response.status_code == 200:
            summary = response.json().get("response", "")
            return summary
        else:
            logger.error(
                f"Error from Ollama API: {response.status_code} {response.text}"
            )
            raise Exception(
                f"Error from Ollama API: {response.status_code} {response.text}"
            )
