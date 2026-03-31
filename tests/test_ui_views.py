import unittest

from src.apps.ui.ui_views import (
    build_force_release_payload,
    build_targeted_release_payload,
    get_snapshot_worker_id,
)


class TestProcessingLockHelpers(unittest.TestCase):
    def test_get_snapshot_worker_id_trims_value(self) -> None:
        worker_id = get_snapshot_worker_id({"worker_id": "  worker-123  "})

        self.assertEqual(worker_id, "worker-123")

    def test_get_snapshot_worker_id_returns_none_for_missing_value(self) -> None:
        self.assertIsNone(get_snapshot_worker_id({}))
        self.assertIsNone(get_snapshot_worker_id({"worker_id": "   "}))

    def test_build_targeted_release_payload_uses_snapshot_worker_when_missing_input(self) -> None:
        payload = build_targeted_release_payload(
            manual_worker_id="",
            snapshot_worker_id="worker-from-snapshot",
            reason="manual cleanup",
        )

        self.assertEqual(
            payload,
            {
                "expected_worker_id": "worker-from-snapshot",
                "reason": "manual cleanup",
            },
        )

    def test_build_targeted_release_payload_prefers_manual_worker(self) -> None:
        payload = build_targeted_release_payload(
            manual_worker_id="worker-manual",
            snapshot_worker_id="worker-from-snapshot",
            reason="",
        )

        self.assertEqual(payload, {"expected_worker_id": "worker-manual"})

    def test_build_targeted_release_payload_returns_none_when_no_worker_available(self) -> None:
        payload = build_targeted_release_payload(
            manual_worker_id="  ",
            snapshot_worker_id=None,
            reason="cleanup",
        )

        self.assertIsNone(payload)

    def test_build_force_release_payload_includes_threshold_and_reason(self) -> None:
        payload = build_force_release_payload(
            reason="reset all locks",
            force_threshold=1800,
        )

        self.assertEqual(
            payload,
            {
                "force": True,
                "force_threshold_seconds": 1800,
                "reason": "reset all locks",
            },
        )


if __name__ == "__main__":
    unittest.main()
