import importlib.util
import json
from pathlib import Path
import tempfile
import unittest


SCRIPT = Path(__file__).parents[1] / "scripts" / "progress.py"
SPEC = importlib.util.spec_from_file_location("weekly_progress", SCRIPT)
progress = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(progress)


class ProgressTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.content = self.root / "apps/showcase/content/weekly-insights"
        self.content.mkdir(parents=True)
        self.series = {"collectionStart": "2026-09-01", "analysisVersion": "v1", "categories": [],
                       "timezone": "Asia/Taipei", "weekConvention": "sunday-saturday",
                       "dateBasis": "notion-created-time", "dedupPolicy": "within-week-source",
                       "reportStarts": []}
        self.snapshot = self.root / "data/reports/snapshot.json"
        self.snapshot.parent.mkdir(parents=True)
        self.snapshot.write_text('{"records": []}')

    def week(self, start, closed=True):
        directory = self.content / start
        directory.mkdir(exist_ok=True)
        report = {"start": start, "endExclusive": str(progress.day(start) + progress.WEEK),
                  "coverageStart": max(start, self.series["collectionStart"]), "analysisVersion": "v1",
                  "published": True, "revision": 1, "dataCompleteness": "complete",
                  "asOf": "2026-10-09T09:44:10Z", "periodState": "closed" if closed else "open"}
        (directory / "report.json").write_text(json.dumps(report))
        (directory / "report.md").write_text("週報內容")
        self.series["reportStarts"].append(start)
        return progress.checkpoint(self.root, self.series, start, self.snapshot)

    def test_default_cutoff_is_last_saturday_and_first_week_starts_sunday(self):
        result = progress.plan(self.root, self.series, {}, "2026-10-09")
        self.assertEqual(result["through"], "2026-10-03")
        self.assertEqual(result["weeks"][0]["start"], "2026-08-30")
        self.assertEqual(result["weeks"][0]["coverageStart"], "2026-09-01")
        self.assertEqual(result["weeks"][-1]["start"], "2026-09-27")

    def test_hole_is_not_skipped_even_when_later_week_finished(self):
        entries = {start: self.week(start) for start in ["2026-08-30", "2026-09-13"]}
        result = progress.plan(self.root, self.series, entries, "2026-09-20")
        self.assertEqual([week["start"] for week in result["weeks"]], ["2026-09-06"])

    def test_open_week_is_revisited_after_it_closes(self):
        entries = {"2026-10-04": self.week("2026-10-04", closed=False)}
        result = progress.plan(self.root, self.series, entries, "2026-10-12", from_date="2026-10-04")
        self.assertEqual(result["weeks"][0]["reason"], "previously-open")

    def test_explicit_midweek_cutoff_requires_open_opt_in(self):
        with self.assertRaises(ValueError):
            progress.plan(self.root, self.series, {}, "2026-10-09", through="2026-10-07")
        result = progress.plan(self.root, self.series, {}, "2026-10-09", through="2026-10-07", include_open=True)
        self.assertEqual(result["weeks"][-1]["coverageThrough"], "2026-10-07")
        self.assertEqual(result["weeks"][-1]["periodState"], "open")

    def test_changed_artifact_version_missing_snapshot_and_refresh_are_scheduled(self):
        entry = self.week("2026-09-06")
        entries = {"2026-09-06": entry}
        args = {"from_date": "2026-09-06", "through": "2026-09-12"}
        self.assertEqual(progress.plan(self.root, self.series, entries, "2026-10-09", **args)["weeks"], [])
        report_path = self.content / "2026-09-06/report.json"
        report = json.loads(report_path.read_text())
        report["asOf"] = "2026-10-10T09:44:10Z"
        report_path.write_text(json.dumps(report))
        self.assertEqual(progress.plan(self.root, self.series, entries, "2026-10-09", **args)["weeks"], [])
        self.assertEqual(progress.plan(self.root, self.series, entries, "2026-10-09", refresh=True, **args)
                         ["weeks"][0]["reason"], "requested-refresh")
        self.snapshot.unlink()
        self.assertEqual(progress.plan(self.root, self.series, entries, "2026-10-09", **args)
                         ["weeks"][0]["reason"], "snapshot-missing")
        self.snapshot.write_text('{"records": []}')
        (self.content / "2026-09-06/report.md").write_text("修改內容")
        self.assertEqual(progress.plan(self.root, self.series, entries, "2026-10-09", **args)
                         ["weeks"][0]["reason"], "artifact-changed")
        self.series["analysisVersion"] = "v2"
        self.assertEqual(progress.plan(self.root, self.series, entries, "2026-10-09", **args)
                         ["weeks"][0]["reason"], "policy-changed")

    def test_failed_checkpoint_does_not_advance_and_future_target_rejected(self):
        self.week("2026-09-06")
        self.snapshot.unlink()
        with self.assertRaises(FileNotFoundError):
            progress.checkpoint(self.root, self.series, "2026-09-06", self.snapshot)
        with self.assertRaises(ValueError):
            progress.plan(self.root, self.series, {}, "2026-10-09", through="2026-10-31")

    def test_year_boundary_and_old_midweek_target_keep_whole_closed_week(self):
        self.series["collectionStart"] = "2026-12-31"
        result = progress.plan(self.root, self.series, {}, "2027-01-13", through="2027-01-05")
        self.assertEqual([week["start"] for week in result["weeks"]], ["2026-12-27", "2027-01-03"])
        self.assertEqual(result["weeks"][-1]["coverageThrough"], "2027-01-09")

    def test_atomic_state_roundtrip_and_series_mismatch(self):
        state = {"schemaVersion": 1, "collectionStart": "2026-09-01", "weeks": {}}
        path = self.root / "data/reports/progress.json"
        progress.save_state(path, state)
        self.assertEqual(progress.load_state(path, self.series)["weeks"], {})
        self.series["collectionStart"] = "2026-09-02"
        with self.assertRaises(ValueError):
            progress.load_state(path, self.series)


if __name__ == "__main__":
    unittest.main()
