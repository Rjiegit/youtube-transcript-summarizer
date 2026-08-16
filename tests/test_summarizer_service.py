import os
import sys
import types
import unittest
from unittest.mock import MagicMock, patch


if "dotenv" not in sys.modules:  # pragma: no cover - testing scaffold
    dotenv_stub = types.ModuleType("dotenv")
    dotenv_stub.load_dotenv = lambda *args, **kwargs: False
    sys.modules["dotenv"] = dotenv_stub

if "google.generativeai" not in sys.modules:  # pragma: no cover
    google_module = sys.modules.setdefault(
        "google",
        types.ModuleType("google"),
    )
    generativeai_stub = types.ModuleType("google.generativeai")
    generativeai_stub.configure = lambda *args, **kwargs: None

    class _GenerativeModel:
        def __init__(self, *_args, **_kwargs):
            pass

        def generate_content(self, *_args, **_kwargs):
            return types.SimpleNamespace(text="stub-gemini")

    generativeai_stub.GenerativeModel = _GenerativeModel
    google_module.generativeai = generativeai_stub
    sys.modules["google.generativeai"] = generativeai_stub

if "openai" not in sys.modules:  # pragma: no cover - testing scaffold
    openai_stub = types.ModuleType("openai")

    class _OpenAI:
        def __init__(self, *args, **kwargs):
            self.chat = types.SimpleNamespace(
                completions=types.SimpleNamespace(
                    create=lambda **_kwargs: types.SimpleNamespace(
                        choices=[
                            types.SimpleNamespace(
                                message=types.SimpleNamespace(
                                    content="stub-openai"
                                )
                            )
                        ]
                    )
                )
            )

    openai_stub.OpenAI = _OpenAI
    sys.modules["openai"] = openai_stub

if "ollama" not in sys.modules:  # pragma: no cover - testing scaffold
    ollama_stub = types.ModuleType("ollama")

    class _Client:
        def __init__(self, *args, **kwargs):
            pass

        def chat(self, *args, **kwargs):
            return types.SimpleNamespace(
                message=types.SimpleNamespace(content="stub-ollama")
            )

    ollama_stub.Client = _Client
    sys.modules["ollama"] = ollama_stub


from src.core.config import Config
from src.infrastructure.llm.model_options import Backend, ModelCandidate
from src.infrastructure.llm import summarizer_service
from src.infrastructure.llm.summarizer_service import Summarizer
from src.infrastructure.llm.weighted_selection import (
    NoAvailableModelCandidateError,
)


class _FixedRng:
    def __init__(self, values):
        self._values = iter(values)

    def random(self):
        return next(self._values)


class TestSummarizerService(unittest.TestCase):
    def test_get_prompt_uses_learning_notes_template(self):
        summarizer = Summarizer()

        result = summarizer.get_prompt("測試影片", "這是逐字稿")

        self.assertIn("# 學習筆記", result)
        self.assertIn("## TL;DR", result)
        self.assertIn("## 快速結論", result)
        self.assertIn("## 這支影片在說什麼", result)
        self.assertIn("## 最重要的 3-5 個重點", result)
        self.assertIn("## 知識架構", result)
        self.assertIn("## 複習問題", result)
        self.assertIn("2-4 段", result)
        self.assertIn("核心主張、理由、影響與可採取的行動", result)
        self.assertIn("測試影片", result)
        self.assertIn("這是逐字稿", result)
        self.assertNotIn("{title}", result)
        self.assertNotIn("{text}", result)

    def test_auto_selects_configured_gemini_candidate(self):
        with patch.dict(
            os.environ,
            {
                "OPENAI_API_KEY": "openai-key",
                "GOOGLE_GEMINI_API_KEY": "gemini-key",
                "OLLAMA_API_KEY": "ollama-key",
            },
            clear=False,
        ):
            summarizer = Summarizer()

        with patch.object(
            Summarizer,
            "summarize_with_google_gemini",
            return_value="gemini-summary",
        ) as mock_gemini:
            result = summarizer.summarize("title", "text")

        self.assertEqual(result, "gemini-summary")
        self.assertEqual(summarizer.last_backend, "gemini")
        self.assertEqual(
            summarizer.last_model_label,
            "gemini:gemini-3.5-flash-lite",
        )
        mock_gemini.assert_called_once_with(
            "title",
            "text",
            model="gemini-3.5-flash-lite",
        )

    def test_provider_key_does_not_enable_model_missing_from_auto_pool(self):
        with patch.dict(
            os.environ,
            {"OPENAI_API_KEY": "openai-key"},
            clear=True,
        ):
            summarizer = Summarizer()

        with self.assertRaises(NoAvailableModelCandidateError):
            summarizer.summarize("title", "text")

    def test_transient_error_reselects_once_and_records_successful_model(self):
        from google.api_core.exceptions import TooManyRequests

        candidates = [
            ModelCandidate(Backend.GEMINI, "gemini-a", 80),
            ModelCandidate(Backend.OPENAI, "openai-a", 20),
        ]
        with patch.dict(
            os.environ,
            {
                "GOOGLE_GEMINI_API_KEY": "gemini-key",
                "OPENAI_API_KEY": "openai-key",
            },
            clear=True,
        ):
            summarizer = Summarizer(
                model_candidates=candidates,
                rng=_FixedRng([0.0, 0.0]),
            )

        with patch.object(
            summarizer,
            "summarize_with_google_gemini",
            side_effect=TooManyRequests("busy"),
        ) as mock_gemini:
            with patch.object(
                summarizer,
                "summarize_with_openai",
                return_value="openai-summary",
            ) as mock_openai:
                result = summarizer.summarize("title", "text")

        self.assertEqual(result, "openai-summary")
        self.assertEqual(summarizer.last_backend, "openai")
        self.assertEqual(summarizer.last_model_label, "openai:openai-a")
        mock_gemini.assert_called_once_with("title", "text", model="gemini-a")
        mock_openai.assert_called_once_with("title", "text", model="openai-a")

    def test_non_transient_error_does_not_switch_candidate(self):
        from google.api_core.exceptions import Unauthorized

        candidates = [
            ModelCandidate(Backend.GEMINI, "gemini-a", 80),
            ModelCandidate(Backend.OPENAI, "openai-a", 20),
        ]
        with patch.dict(
            os.environ,
            {
                "GOOGLE_GEMINI_API_KEY": "gemini-key",
                "OPENAI_API_KEY": "openai-key",
            },
            clear=True,
        ):
            summarizer = Summarizer(
                model_candidates=candidates,
                rng=_FixedRng([0.0]),
            )

        with patch.object(
            summarizer,
            "summarize_with_google_gemini",
            side_effect=Unauthorized("bad key"),
        ):
            with patch.object(
                summarizer,
                "summarize_with_openai",
            ) as mock_openai:
                with self.assertRaises(Unauthorized):
                    summarizer.summarize("title", "text")

        mock_openai.assert_not_called()

    def test_transient_error_without_fallback_preserves_original_error(self):
        from google.api_core.exceptions import TooManyRequests

        original_error = TooManyRequests("busy")
        with patch.dict(
            os.environ,
            {"GOOGLE_GEMINI_API_KEY": "gemini-key"},
            clear=True,
        ):
            summarizer = Summarizer(rng=_FixedRng([0.0]))

        with patch.object(
            summarizer,
            "summarize_with_google_gemini",
            side_effect=original_error,
        ):
            with self.assertRaises(TooManyRequests) as raised:
                summarizer.summarize("title", "text")

        self.assertIs(raised.exception, original_error)

    def test_fallback_is_attempted_only_once(self):
        from google.api_core.exceptions import TooManyRequests

        candidates = [
            ModelCandidate(Backend.GEMINI, "gemini-a", 80),
            ModelCandidate(Backend.OPENAI, "openai-a", 15),
            ModelCandidate(Backend.OLLAMA, "ollama-a", 5),
        ]
        with patch.dict(
            os.environ,
            {
                "GOOGLE_GEMINI_API_KEY": "gemini-key",
                "OPENAI_API_KEY": "openai-key",
                "OLLAMA_API_KEY": "ollama-key",
            },
            clear=True,
        ):
            summarizer = Summarizer(
                model_candidates=candidates,
                rng=_FixedRng([0.0, 0.0]),
            )

        fallback_error = RuntimeError("fallback failed")
        with patch.object(
            summarizer,
            "summarize_with_google_gemini",
            side_effect=TooManyRequests("busy"),
        ):
            with patch.object(
                summarizer,
                "summarize_with_openai",
                side_effect=fallback_error,
            ) as mock_openai:
                with patch.object(
                    summarizer,
                    "summarize_with_ollama",
                ) as mock_ollama:
                    with self.assertRaises(RuntimeError) as raised:
                        summarizer.summarize("title", "text")

        self.assertIs(raised.exception, fallback_error)
        mock_openai.assert_called_once()
        mock_ollama.assert_not_called()

    def test_openai_transient_error_is_classified_for_fallback(self):
        class FakeRateLimitError(Exception):
            pass

        summarizer = Summarizer()
        with patch.object(
            summarizer_service.openai,
            "RateLimitError",
            FakeRateLimitError,
            create=True,
        ):
            is_transient = summarizer._is_transient_provider_error(
                Backend.OPENAI,
                FakeRateLimitError("busy"),
            )

        self.assertTrue(is_transient)

    def test_ollama_retries_429_and_5xx_but_not_regular_4xx(self):
        class FakeResponseError(Exception):
            def __init__(self, status_code):
                self.status_code = status_code

        fake_ollama = types.SimpleNamespace(ResponseError=FakeResponseError)
        summarizer = Summarizer()
        with patch.object(
            summarizer_service,
            "ollama_module",
            fake_ollama,
        ):
            for status_code in (429, 500, 503):
                with self.subTest(status_code=status_code):
                    self.assertTrue(
                        summarizer._is_transient_provider_error(
                            Backend.OLLAMA,
                            FakeResponseError(status_code),
                        )
                    )
            self.assertFalse(
                summarizer._is_transient_provider_error(
                    Backend.OLLAMA,
                    FakeResponseError(400),
                )
            )

    def test_summarize_with_ollama_uses_cloud_client(self):
        with patch.dict(
            os.environ,
            {
                "OLLAMA_API_KEY": "ollama-key",
                "OLLAMA_HOST": "https://ollama.com",
            },
            clear=True,
        ):
            summarizer = Summarizer()

        fake_response = types.SimpleNamespace(
            message=types.SimpleNamespace(content=" cloud summary ")
        )
        fake_client = MagicMock()
        fake_client.chat.return_value = fake_response

        with patch(
            "src.infrastructure.llm.summarizer_service.OllamaClient",
            return_value=fake_client,
        ) as mock_client:
            result = summarizer.summarize_with_ollama(
                "title",
                "text",
                model="kimi-k2.5:cloud",
            )

        self.assertEqual(result, "cloud summary")
        self.assertEqual(summarizer.last_backend, "ollama")
        self.assertEqual(summarizer.last_model_label, "ollama:kimi-k2.5:cloud")
        mock_client.assert_called_once_with(
            host="https://ollama.com",
            headers={"Authorization": "Bearer ollama-key"},
        )
        fake_client.chat.assert_called_once()
        self.assertEqual(
            fake_client.chat.call_args.kwargs["model"],
            "kimi-k2.5:cloud",
        )

    def test_config_validate_accepts_ollama_only(self):
        with patch.dict(
            os.environ,
            {
                "OLLAMA_API_KEY": "ollama-key",
                "OPENAI_API_KEY": "",
                "GOOGLE_GEMINI_API_KEY": "",
            },
            clear=True,
        ):
            config = Config()

        config.validate()


if __name__ == "__main__":
    unittest.main()
