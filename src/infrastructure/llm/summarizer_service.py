import os
import random
import time
from collections.abc import Iterable

from dotenv import load_dotenv
import google.generativeai as genai
import openai
from openai import OpenAI

from src.core import prompt
from src.core.logger import logger
from src.infrastructure.llm.model_options import (
    AUTO_MODEL_CANDIDATES,
    Backend,
    GEMINI_MODEL,
    ModelCandidate,
    OLLAMA_MODEL,
    OPENAI_MODEL,
    PROVIDER_SETTINGS,
)
from src.infrastructure.llm.weighted_selection import (
    NoAvailableModelCandidateError,
    choose_weighted_candidate,
    validate_model_candidates,
)

try:
    from google.api_core import exceptions as google_api_exceptions
except ImportError:  # pragma: no cover - dependency fallback
    google_api_exceptions = None

try:
    import httpx
except ImportError:  # pragma: no cover - dependency fallback
    httpx = None

try:
    import ollama as ollama_module
    from ollama import Client as OllamaClient
except ImportError:  # pragma: no cover - optional dependency in minimal envs
    ollama_module = None
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
    def __init__(
        self,
        *,
        model_candidates: Iterable[ModelCandidate] | None = None,
        rng=None,
    ):
        configured_candidates = (
            AUTO_MODEL_CANDIDATES
            if model_candidates is None
            else model_candidates
        )
        self.model_candidates = validate_model_candidates(
            configured_candidates
        )
        self.rng = rng or random

        self._api_keys = {
            backend: os.getenv(settings.api_key_env)
            for backend, settings in PROVIDER_SETTINGS.items()
        }
        # Preserve these attributes for provider-specific methods and callers.
        self.openai_api_key = self._api_keys[Backend.OPENAI]
        self.google_gemini_api_key = self._api_keys[Backend.GEMINI]
        self.ollama_api_key = self._api_keys[Backend.OLLAMA]
        self.ollama_host = os.getenv("OLLAMA_HOST", "https://ollama.com")
        self.last_backend = None
        self.last_model_label = None

    def summarize(self, title, text):
        if self._is_test_mode(text):
            self.last_backend = "mock"
            self.last_model_label = "mock"
            return self._mock_summarize(title, text)

        candidate = self._choose_candidate()
        try:
            return self._summarize_with_candidate(candidate, title, text)
        except Exception as first_error:
            if not self._is_transient_provider_error(
                candidate.backend,
                first_error,
            ):
                raise

            logger.warning(
                f"[Auto] Transient failure "
                f"backend={candidate.backend.value} model={candidate.model} "
                f"error={type(first_error).__name__}; selecting fallback"
            )
            fallback = self._choose_fallback(candidate)
            if fallback is None:
                logger.warning(
                    "[Auto] No alternative candidate is available; "
                    "re-raising the original error"
                )
                raise

            try:
                return self._summarize_with_candidate(fallback, title, text)
            except Exception as second_error:
                logger.error(
                    f"[Auto] Fallback failed "
                    f"backend={fallback.backend.value} model={fallback.model} "
                    f"error={type(second_error).__name__}"
                )
                raise

    def _available_backends(self) -> set[Backend]:
        return {
            backend
            for backend, api_key in self._api_keys.items()
            if api_key and api_key.strip()
        }

    def _choose_candidate(
        self,
        *,
        excluded: set[tuple[Backend, str]] | None = None,
    ) -> ModelCandidate:
        selected = choose_weighted_candidate(
            self.model_candidates,
            available_backends=self._available_backends(),
            excluded=excluded,
            rng=self.rng,
        )
        logger.info(
            f"[Auto] Selected backend={selected.backend.value} "
            f"model={selected.model} weight={selected.weight}"
        )
        return selected

    def _choose_fallback(
        self,
        failed_candidate: ModelCandidate,
    ) -> ModelCandidate | None:
        try:
            return self._choose_candidate(excluded={failed_candidate.key})
        except NoAvailableModelCandidateError:
            return None

    def _summarize_with_candidate(
        self,
        candidate: ModelCandidate,
        title: str,
        text: str,
    ) -> str:
        self.last_backend = candidate.backend.value
        self.last_model_label = self._format_model_label(
            candidate.backend,
            candidate.model,
        )
        logger.info(
            f"[Summarizer] backend={candidate.backend.value} "
            f"model={candidate.model}"
        )

        if candidate.backend == Backend.GEMINI:
            return self.summarize_with_google_gemini(
                title,
                text,
                model=candidate.model,
            )
        if candidate.backend == Backend.OPENAI:
            return self.summarize_with_openai(
                title,
                text,
                model=candidate.model,
            )
        if candidate.backend == Backend.OLLAMA:
            return self.summarize_with_ollama(
                title,
                text,
                model=candidate.model,
            )
        raise ValueError(f"Unsupported backend: {candidate.backend}")

    def _is_transient_provider_error(
        self,
        backend: Backend,
        error: Exception,
    ) -> bool:
        if backend == Backend.OPENAI:
            if self._is_instance_of_named_types(
                error,
                openai,
                (
                    "RateLimitError",
                    "APITimeoutError",
                    "APIConnectionError",
                    "InternalServerError",
                ),
            ):
                return True
            api_status_error = getattr(openai, "APIStatusError", None)
            return bool(
                api_status_error
                and isinstance(error, api_status_error)
                and getattr(error, "status_code", 0) >= 500
            )

        if backend == Backend.GEMINI and google_api_exceptions:
            return self._is_instance_of_named_types(
                error,
                google_api_exceptions,
                (
                    "TooManyRequests",
                    "DeadlineExceeded",
                    "ServiceUnavailable",
                    "InternalServerError",
                    "ServerError",
                ),
            )

        if backend == Backend.OLLAMA:
            timeout_types = (TimeoutError, ConnectionError)
            if httpx:
                timeout_types += (httpx.TimeoutException,)
            if isinstance(error, timeout_types):
                return True
            response_error = (
                getattr(ollama_module, "ResponseError", None)
                if ollama_module
                else None
            )
            if response_error and isinstance(error, response_error):
                status_code = getattr(error, "status_code", -1)
                return status_code == 429 or status_code >= 500

        return False

    @staticmethod
    def _is_instance_of_named_types(
        error: Exception,
        module,
        names: tuple[str, ...],
    ) -> bool:
        exception_types = tuple(
            exception_type
            for name in names
            if isinstance(
                exception_type := getattr(module, name, None),
                type,
            )
        )
        return bool(exception_types and isinstance(error, exception_types))

    def _format_model_label(
        self,
        backend: Backend | str,
        model: str,
    ) -> str:
        backend_name = (
            backend.value if isinstance(backend, Backend) else backend
        )
        if backend_name == "mock":
            return "mock"
        return f"{backend_name}:{model}"

    def _is_test_mode(self, text):
        """檢測是否為測試模式"""
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

        if TestSampleManager is None:
            logger.warning("[測試模式] TestSampleManager 不可用，使用基本模擬")
            time.sleep(random.uniform(0.8, 1.5))
            return f"[測試模式摘要] {title}\n\n這是一個模擬的摘要內容，用於測試目的。"

        time.sleep(random.uniform(0.8, 1.5))

        sample_manager = TestSampleManager()
        if sample_manager.simulate_error():
            error_msg = sample_manager.get_random_error_message()
            logger.error(f"[測試模式] 模擬摘要錯誤: {error_msg}")
            raise Exception(f"[測試模式] {error_msg}")

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
        model: str = GEMINI_MODEL,
    ):
        if not self.google_gemini_api_key:
            raise ValueError(
                "API key is not set. Please add it to the .env file."
            )

        genai.configure(api_key=self.google_gemini_api_key)
        self.last_backend = "gemini"
        self.last_model_label = self._format_model_label("gemini", model)
        gemini = genai.GenerativeModel(model)
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
