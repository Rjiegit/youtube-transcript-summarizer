import io
import json
import unittest
from contextlib import redirect_stderr, redirect_stdout
from datetime import datetime, timezone
from unittest.mock import patch

from whisper_summary.core.logger import logger


class LoggerTests(unittest.TestCase):
    def test_levels_use_taipei_time_across_date_boundary(self):
        instant = datetime(2026, 10, 24, 20, 30, 45, 123000, tzinfo=timezone.utc)
        for level in ("info", "warning", "error"):
            with self.subTest(level=level):
                output = io.StringIO()
                with patch("whisper_summary.core.logger.datetime") as clock, redirect_stdout(output):
                    clock.now.side_effect = lambda tz: instant.astimezone(tz)
                    getattr(logger, level)('測試訊息\n"第二行"')
                self.assertEqual(len(output.getvalue().splitlines()), 1)
                self.assertEqual(json.loads(output.getvalue()), {
                    "timestamp": "2026-10-25T04:30:45.123+08:00",
                    "level": level.upper(),
                    "message": '測試訊息\n"第二行"',
                })

    def test_exception_keeps_traceback_in_single_json_record(self):
        output, errors = io.StringIO(), io.StringIO()
        with redirect_stdout(output), redirect_stderr(errors):
            try:
                raise ValueError("測試錯誤")
            except ValueError:
                logger.exception("處理失敗")
        self.assertEqual(len(output.getvalue().splitlines()), 1)
        record = json.loads(output.getvalue())
        self.assertEqual(record["level"], "ERROR")
        self.assertEqual(record["message"], "處理失敗")
        self.assertEqual(datetime.fromisoformat(record["timestamp"]).utcoffset().total_seconds(), 28800)
        self.assertIn("Traceback (most recent call last):", record["exception"])
        self.assertIn("ValueError: 測試錯誤", record["exception"])
        self.assertEqual(errors.getvalue(), "")

    def test_non_string_messages_remain_supported(self):
        output = io.StringIO()
        with redirect_stdout(output):
            logger.info(123)
        self.assertEqual(json.loads(output.getvalue())["message"], "123")
