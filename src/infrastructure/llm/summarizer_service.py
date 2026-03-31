import os
from dotenv import load_dotenv
import google.generativeai as genai
from openai import OpenAI
from src.core import prompt
from src.core.logger import logger
from src.infrastructure.llm.model_options import (
    AUTO_SUMMARIZER_MODELS,
    GEMINI_MODEL,
    GEMINI_WEIGHTED_MODELS,
    OLLAMA_MODEL,
    OLLAMA_WEIGHTED_MODELS,
    OPENAI_MODEL,
)
import time
import random

from src.infrastructure.llm.weighted_selection import (
    choose_weighted_backend_model,
    choose_weighted_model,
)

try:
    from ollama import Client as OllamaClient
except ImportError:  # pragma: no cover - optional dependency in minimal envs
    OllamaClient = None

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
        self.ollama_api_key = os.getenv("OLLAMA_API_KEY")
        self.ollama_host = os.getenv("OLLAMA_HOST", "https://ollama.com")
        # Keep last-used backend/model label for callers
        self.last_backend = None
        self.last_model_label = None

    def summarize(self, title, text):
        # Decide backend based on environment and test mode
        selection_mode = self._determine_backend(text)

        if selection_mode == "mock":
            self.last_backend = "mock"
            self.last_model_label = self._format_model_label("mock", "mock")
            return self._mock_summarize(title, text)
        if selection_mode == "unknown":
            raise ValueError(
                "No available summarization backend "
                "(set API keys or enable test mode)"
            )

        backend, model = self._choose_backend_and_model(selection_mode)
        self.last_backend = backend
        self.last_model_label = self._format_model_label(backend, model)
        logger.info(
            f"[Summarizer] selection_mode={selection_mode} "
            f"backend={backend} model={model}"
        )

        if backend == "gemini":
            return self.summarize_with_google_gemini(title, text, model=model)
        if backend == "openai":
            return self.summarize_with_openai(title, text, model=model)
        if backend == "ollama":
            return self.summarize_with_ollama(title, text, model=model)
        raise ValueError(
            "No available summarization backend "
            "(set API keys or enable test mode)"
        )

    def _determine_backend(self, text):
        if self._is_test_mode(text):
            return "mock"
        available_backends = self._available_backends()
        if len(available_backends) > 1:
            return "auto"
        if available_backends:
            return available_backends[0]
        return "unknown"

    def _available_backends(self) -> list[str]:
        available = []
        if self.google_gemini_api_key:
            available.append("gemini")
        if self.openai_api_key:
            available.append("openai")
        if self.ollama_api_key:
            available.append("ollama")
        return available

    def _format_model_label(self, backend: str, model: str) -> str:
        if backend == "mock":
            return "mock"
        return f"{backend}:{model}"

    def _choose_backend_and_model(
        self,
        selection_mode: str,
    ) -> tuple[str, str]:
        if selection_mode == "auto":
            return self._choose_auto_backend_and_model()

        if selection_mode == "gemini":
            return "gemini", self._choose_gemini_model()
        if selection_mode == "openai":
            return "openai", OPENAI_MODEL
        if selection_mode == "ollama":
            return "ollama", self._choose_ollama_model()

        raise ValueError(f"Unsupported selection mode: {selection_mode}")

    def _choose_auto_backend_and_model(self) -> tuple[str, str]:
        available_backends = set(self._available_backends())
        candidates = [
            candidate
            for candidate in AUTO_SUMMARIZER_MODELS
            if candidate.backend in available_backends
        ]
        selected = choose_weighted_backend_model(candidates, rng=random)
        logger.info(
            f"[Auto] Selected backend={selected.backend} model={selected.model}"
        )
        return selected.backend, selected.model

    def _choose_gemini_model(self) -> str:
        selected_model = GEMINI_MODEL
        if GEMINI_WEIGHTED_MODELS:
            try:
                selected_model = choose_weighted_model(
                    GEMINI_WEIGHTED_MODELS,
                    rng=random,
                )
            except ValueError:
                selected_model = GEMINI_MODEL
        logger.info(f"[Gemini] Selected model: {selected_model}")
        return selected_model

    def _choose_ollama_model(self) -> str:
        selected_model = OLLAMA_MODEL
        if OLLAMA_WEIGHTED_MODELS:
            try:
                selected_model = choose_weighted_model(
                    OLLAMA_WEIGHTED_MODELS,
                    rng=random,
                )
            except ValueError:
                selected_model = OLLAMA_MODEL
        logger.info(f"[Ollama] Selected model: {selected_model}")
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
        return prompt.PROMPT_VIDEO_SUMMARY.format(title=title, text=text)

    def summarize_with_openai(self, title, text, model: str = OPENAI_MODEL):
        if not self.openai_api_key:
            raise ValueError(
                "API key is not set. Please add it to the .env file."
            )

        self.last_backend = "openai"
        self.last_model_label = self._format_model_label("openai", model)
        client = OpenAI(api_key=self.openai_api_key)
        prompt_text = self.get_prompt(title=title, text=text)
        resp = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": prompt_text},
            ],
            temperature=0.5,
        )
        return resp.choices[0].message.content.strip()

    def summarize_with_google_gemini(
        self,
        title,
        text,
        model: str | None = None,
    ):
        if not self.google_gemini_api_key:
            raise ValueError(
                "API key is not set. Please add it to the .env file."
            )

        genai.configure(api_key=self.google_gemini_api_key)

        selected_model = model or self._choose_gemini_model()
        self.last_backend = "gemini"
        self.last_model_label = self._format_model_label(
            "gemini",
            selected_model,
        )
        gemini = genai.GenerativeModel(selected_model)
        response = gemini.generate_content(
            self.get_prompt(title=title, text=text)
        )

        return response.text

    def summarize_with_ollama(self, title, text, model: str = OLLAMA_MODEL):
        if not self.ollama_api_key:
            raise ValueError(
                "OLLAMA_API_KEY is not set. Please add it to the .env file."
            )
        if OllamaClient is None:
            raise ImportError(
                "ollama package is not installed. "
                "Please install project dependencies."
            )

        self.last_backend = "ollama"
        self.last_model_label = self._format_model_label("ollama", model)
        logger.info(
            f"[Ollama] Summarize with host={self.ollama_host} "
            f"model={model}"
        )
        client = OllamaClient(
            host=self.ollama_host,
            headers={"Authorization": f"Bearer {self.ollama_api_key}"},
        )
        response = client.chat(
            model=model,
            messages=[
                {
                    "role": "user",
                    "content": self.get_prompt(title=title, text=text),
                }
            ],
        )
        return response.message.content.strip()
