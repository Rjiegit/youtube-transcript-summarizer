import unittest

from discord_notifier import RequestException, send_task_completion_notification


class _StubResponse:
    def __init__(self, status_code: int, text: str = ""):
        self.status_code = status_code
        self.text = text


class TestDiscordNotifier(unittest.TestCase):
    def test_send_notification_success(self):
        def stub_post(webhook_url, *, json, timeout):
            self.assertEqual(webhook_url, "https://discord.example/webhook")
            self.assertIn("content", json)
            self.assertEqual(timeout, 10)
            return _StubResponse(204, "ok")

        result = send_task_completion_notification(
            "Title", "https://youtu.be/id", "https://discord.example/webhook", post=stub_post
        )
        self.assertTrue(result)

    def test_send_notification_failure_status(self):
        def stub_post(*_, **__):
            return _StubResponse(500, "error")

        result = send_task_completion_notification(
            "Title", "https://youtu.be/id", "https://discord.example/webhook", post=stub_post
        )
        self.assertFalse(result)

    def test_send_notification_exception(self):
        def stub_post(*_, **__):
            raise RequestException("boom")

        result = send_task_completion_notification(
            "Title", "https://youtu.be/id", "https://discord.example/webhook", post=stub_post
        )
        self.assertFalse(result)

    def test_send_notification_missing_webhook(self):
        result = send_task_completion_notification(
            "Title", "https://youtu.be/id", None
        )
        self.assertFalse(result)


if __name__ == "__main__":
    unittest.main()
