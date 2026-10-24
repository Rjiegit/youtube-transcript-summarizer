import os
import types
import unittest
from unittest.mock import patch

from whisper_summary.scripts import list_models


class TestListModels(unittest.TestCase):
    def test_lists_models_with_configured_key_and_closes_client(self):
        models = [types.SimpleNamespace(name="models/gemini-test")]
        with patch.dict(os.environ, {"GOOGLE_GEMINI_API_KEY": "test-key"}, clear=True):
            with patch.object(list_models, "load_dotenv"), patch.object(list_models.genai, "Client") as factory:
                factory.return_value.__enter__.return_value.models.list.return_value = models
                with patch.object(list_models.pprint, "pprint") as output:
                    list_models.main()
        factory.assert_called_once_with(api_key="test-key")
        factory.return_value.__enter__.return_value.models.list.assert_called_once_with()
        output.assert_called_once_with(models[0])
        factory.return_value.__exit__.assert_called_once()

    def test_missing_key_fails_before_creating_client(self):
        with patch.dict(os.environ, {}, clear=True), patch.object(list_models, "load_dotenv"):
            with patch.object(list_models.genai, "Client") as factory:
                with self.assertRaisesRegex(ValueError, "GOOGLE_GEMINI_API_KEY is not set"):
                    list_models.main()
        factory.assert_not_called()
