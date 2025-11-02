import unittest
from unittest.mock import patch

from discord_notifier import RequestException, send_task_completion_notification


class _StubResponse:
    def __init__(self, status_code: int, text: str = ""):
        self.status_code = status_code
        self.text = text


class TestDiscordNotifier(unittest.TestCase):
    def test_send_notification_success(self):
        captured = {}

        def stub_post(webhook_url, *, json, timeout):
            self.assertEqual(webhook_url, "https://discord.example/webhook")
            self.assertEqual(timeout, 10)
            captured["content"] = json["content"]
            return _StubResponse(204, "ok")

        result = send_task_completion_notification(
            "Title",
            "https://youtu.be/id",
            "https://discord.example/webhook",
            notion_url="https://www.notion.so/workspace",
            notion_task_id="12345678-1234-1234-1234-1234567890ab",
            post=stub_post,
        )
        self.assertTrue(result)
        self.assertEqual(
            captured["content"],
            (
                "✅ 任務完成：Title\n"
                "https://youtu.be/id\n"
                "Notion：https://www.notion.so/workspace/123456781234123412341234567890ab"
            ),
        )

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

    def test_send_notification_missing_notion_inputs_logs_info(self):
        captured = {}

        def stub_post(webhook_url, *, json, timeout):
            captured["content"] = json["content"]
            return _StubResponse(204, "ok")

        with patch("discord_notifier.logger") as mock_logger:
            mock_logger.warning = mock_logger.warning  # attribute to avoid AttributeError
            result = send_task_completion_notification(
                "Title",
                "https://youtu.be/id",
                "https://discord.example/webhook",
                notion_url="https://www.notion.so/workspace",
                post=stub_post,
            )

        self.assertTrue(result)
        self.assertEqual(
            captured["content"],
            "✅ 任務完成：Title\nhttps://youtu.be/id",
        )
        mock_logger.info.assert_any_call(
            "Notion link information incomplete; sending Discord notification without Notion URL."
        )


if __name__ == "__main__":
    unittest.main()
