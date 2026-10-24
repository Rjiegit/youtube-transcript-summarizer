import unittest
from unittest.mock import patch

from whisper_summary.infrastructure.media.transcription.transcriber import Transcriber


class _InfoWithDuration:
    def __init__(self, duration=None, duration_ms=None):
        self.duration = duration
        self.duration_ms = duration_ms


class TestTranscriptionProgress(unittest.TestCase):
    def setUp(self):
        self.transcriber = Transcriber()

    def test_transcribe_uses_faster_whisper(self):
        with patch.object(self.transcriber, "_is_test_mode", return_value=False):
            with patch.object(self.transcriber, "transcribe_with_faster_whisper", return_value="轉錄文字") as transcribe:
                self.assertEqual(self.transcriber.transcribe("audio.wav"), "轉錄文字")
        transcribe.assert_called_once_with("audio.wav")

    def test_get_total_duration_seconds_prefers_duration(self):
        info = _InfoWithDuration(duration=123.4, duration_ms=9999)
        self.assertEqual(self.transcriber._get_total_duration_seconds(info), 123.4)

    def test_get_total_duration_seconds_falls_back_to_duration_ms(self):
        info = _InfoWithDuration(duration=None, duration_ms=2500)
        self.assertEqual(self.transcriber._get_total_duration_seconds(info), 2.5)

    def test_get_progress_updates_emits_milestones(self):
        updates, next_progress = self.transcriber._get_progress_updates(
            segment_end=25.0,
            total_duration=100.0,
            next_progress=10,
        )
        self.assertEqual(updates, [10, 20])
        self.assertEqual(next_progress, 30)

    def test_get_progress_updates_handles_large_jump(self):
        updates, next_progress = self.transcriber._get_progress_updates(
            segment_end=95.0,
            total_duration=100.0,
            next_progress=30,
        )
        self.assertEqual(updates, [30, 40, 50, 60, 70, 80, 90])
        self.assertEqual(next_progress, 100)


if __name__ == "__main__":
    unittest.main()
