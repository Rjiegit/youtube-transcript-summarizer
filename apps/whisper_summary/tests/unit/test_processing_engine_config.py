import os
import unittest
from unittest.mock import patch

from whisper_summary.core.config import Config


class TestProcessingEngineConfig(unittest.TestCase):
    def test_defaults_to_legacy(self) -> None:
        with patch.dict(os.environ, {}, clear=True):
            self.assertEqual(Config().processing_engine, "legacy")

    def test_accepts_langgraph_case_insensitively(self) -> None:
        with patch.dict(os.environ, {"PROCESSING_ENGINE": " LangGraph "}, clear=True):
            self.assertEqual(Config().processing_engine, "langgraph")

    def test_rejects_unknown_engine(self) -> None:
        with patch.dict(os.environ, {"PROCESSING_ENGINE": "other"}, clear=True):
            with self.assertRaisesRegex(ValueError, "PROCESSING_ENGINE"):
                Config()


if __name__ == "__main__":
    unittest.main()
