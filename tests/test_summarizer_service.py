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
from src.infrastructure.llm.summarizer_service import Summarizer


class TestSummarizerService(unittest.TestCase):
    def test_get_prompt_uses_learning_notes_template(self):
        summarizer = Summarizer()

        result = summarizer.get_prompt("測試影片", "這是逐字稿")

        self.assertIn("# 學習筆記", result)
        self.assertIn("## 一句話總結", result)
        self.assertIn("## 知識架構", result)
        self.assertIn("## 複習問題", result)
        self.assertIn("測試影片", result)
        self.assertIn("這是逐字稿", result)
        self.assertNotIn("{title}", result)
        self.assertNotIn("{text}", result)

    def test_auto_selects_kimi_cloud_and_records_label(self):
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

        with patch(
            "src.infrastructure.llm.summarizer_service.random.random",
            return_value=0.95,
        ):
            with patch.object(
                Summarizer,
                "summarize_with_ollama",
                return_value="ollama-summary",
            ) as mock_ollama:
                result = summarizer.summarize("title", "text")

        self.assertEqual(result, "ollama-summary")
        self.assertEqual(summarizer.last_backend, "ollama")
        self.assertEqual(summarizer.last_model_label, "ollama:kimi-k2.5:cloud")
        mock_ollama.assert_called_once_with(
            "title",
            "text",
            model="kimi-k2.5:cloud",
        )

    def test_single_ollama_backend_uses_weighted_ollama_model(self):
        with patch.dict(
            os.environ,
            {"OLLAMA_API_KEY": "ollama-key"},
            clear=True,
        ):
            summarizer = Summarizer()

        with patch(
            "src.infrastructure.llm.summarizer_service.random.random",
            return_value=0.1,
        ):
            with patch.object(
                Summarizer,
                "summarize_with_ollama",
                return_value="ollama-only-summary",
            ) as mock_ollama:
                result = summarizer.summarize("title", "text")

        self.assertEqual(result, "ollama-only-summary")
        self.assertEqual(summarizer.last_backend, "ollama")
        self.assertEqual(summarizer.last_model_label, "ollama:kimi-k2.5:cloud")
        mock_ollama.assert_called_once_with(
            "title",
            "text",
            model="kimi-k2.5:cloud",
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
