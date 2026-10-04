import unittest
from unittest.mock import patch

from whisper_summary.infrastructure.notifications.discord import (
    RequestException,
    send_task_completion_notification,
)


class _StubResponse:
    def __init__(self, status_code: int, text: str = ""):
        self.status_code = status_code
        self.text = text


class TestDiscordNotifier(unittest.TestCase):
    def test_showcase_link_is_independent_of_notion_url(self):
        for page_id in ("12345678-1234-1234-1234-1234567890ab", "123456781234123412341234567890ab"):
            with self.subTest(page_id=page_id):
                captured = {}

                def stub_post(*_, json, **__):
                    captured.update(json)
                    return _StubResponse(204)

                self.assertTrue(send_task_completion_notification(
                    "Title", "https://youtu.be/id", "https://discord.example/webhook",
                    showcase_base_url=" https://knowledge.example.com/ ",
                    notion_task_id=page_id, post=stub_post,
                ))
                self.assertEqual(captured["content"], (
                    "✅ 任務完成：Title\nhttps://youtu.be/id\n"
                    "知識庫：https://knowledge.example.com/results/12345678-1234-1234-1234-1234567890ab"
                ))

    def test_invalid_showcase_inputs_preserve_original_notification(self):
        cases = [
            (None, "12345678-1234-1234-1234-1234567890ab"),
            ("https://example.com", None),
            ("https://example.com", "mock_page_123"),
            ("javascript:alert(1)", "12345678-1234-1234-1234-1234567890ab"),
            ("https://example.com?query=1", "12345678-1234-1234-1234-1234567890ab"),
            ("https://example.com#fragment", "12345678-1234-1234-1234-1234567890ab"),
            ("https://user:password@example.com", "12345678-1234-1234-1234-1234567890ab"),
            ("https://[invalid", "12345678-1234-1234-1234-1234567890ab"),
        ]
        for base_url, page_id in cases:
            with self.subTest(base_url=base_url, page_id=page_id):
                captured = {}

                def stub_post(*_, json, **__):
                    captured.update(json)
                    return _StubResponse(204)

                self.assertTrue(send_task_completion_notification(
                    "Title", "https://youtu.be/id", "https://discord.example/webhook",
                    showcase_base_url=base_url, notion_task_id=page_id, post=stub_post,
                ))
                self.assertEqual(captured["content"], "✅ 任務完成：Title\nhttps://youtu.be/id")

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
            showcase_base_url="https://knowledge.example.com",
            post=stub_post,
        )
        self.assertTrue(result)
        self.assertEqual(
            captured["content"],
            (
                "✅ 任務完成：Title\n"
                "https://youtu.be/id\n"
                "知識庫：https://knowledge.example.com/results/12345678-1234-1234-1234-1234567890ab\n"
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

        with patch("whisper_summary.infrastructure.notifications.discord.logger") as mock_logger:
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
