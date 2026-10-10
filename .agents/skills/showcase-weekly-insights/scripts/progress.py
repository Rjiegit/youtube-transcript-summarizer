"""Plan resumable Sunday-based reports; record only locally validated artifacts."""

import argparse
from datetime import date, datetime, timedelta
import hashlib
import json
import os
from pathlib import Path
import subprocess
import tempfile
from zoneinfo import ZoneInfo


WEEK = timedelta(days=7)
TAIPEI = ZoneInfo("Asia/Taipei")
CONTENT = Path("apps/showcase/content/weekly-insights")
STATE = Path("data/reports/weekly-insights/progress.json")


def day(value):
    result = date.fromisoformat(value)
    if result.isoformat() != value:
        raise ValueError("日期必須是 YYYY-MM-DD")
    return result


def sunday(value):
    return value - timedelta(days=(value.weekday() + 1) % 7)


def read_json(path):
    return json.loads(path.read_text(encoding="utf-8"))


def policy(series):
    fields = ("collectionStart", "analysisVersion", "categories", "timezone", "weekConvention", "dateBasis", "dedupPolicy")
    value = json.dumps({key: series[key] for key in fields}, sort_keys=True, ensure_ascii=False)
    return hashlib.sha256(value.encode()).hexdigest()


def matches_policy(series, recorded_hash):
    if recorded_hash == policy(series):
        return True
    # Only the creation-time policy name changed; all other fields must still match.
    if series["dateBasis"] == "record-created-time":
        legacy = {**series, "dateBasis": "notion-created-time"}
        return recorded_hash == policy(legacy)
    return False


def artifact_hash(root, start):
    directory = root / CONTENT / start
    digest = hashlib.sha256()
    report = read_json(directory / "report.json")
    # The website requires a shared asOf; syncing it does not redo closed-week analysis.
    for name in ("asOf", "publishedAt"):
        report.pop(name, None)
    digest.update(json.dumps(report, sort_keys=True, ensure_ascii=False).encode())
    digest.update((directory / "report.md").read_bytes())
    return digest.hexdigest()


def checkpoint(root, series, start, snapshot):
    start_day = day(start)
    if sunday(start_day) != start_day or start not in series["reportStarts"]:
        raise ValueError("週報必須是 manifest 內的週日日期")
    report = read_json(root / CONTENT / start / "report.json")
    as_of = datetime.fromisoformat(report["asOf"].replace("Z", "+00:00"))
    if as_of.tzinfo is None:
        raise ValueError("asOf 必須含時區")
    end = start_day + WEEK
    expected_state = "closed" if as_of.astimezone(TAIPEI).date() >= end else "open"
    if (report["start"] != start or report["endExclusive"] != str(end)
            or report["coverageStart"] != max(start, series["collectionStart"])
            or report["analysisVersion"] != series["analysisVersion"]
            or report["periodState"] != expected_state or report["dataCompleteness"] != "complete"
            or report["published"] is not True):
        raise ValueError("週報未完成本機展示核對，不能登記進度")
    snapshot = snapshot.resolve()
    snapshot_relative = snapshot.relative_to((root / "data/reports").resolve())
    snapshot_bytes = snapshot.read_bytes()
    read_json(snapshot)
    return {
        "status": expected_state,
        "asOf": report["asOf"],
        "revision": report["revision"],
        "policyHash": policy(series),
        "artifactHash": artifact_hash(root, start),
        "snapshot": str(Path("data/reports") / snapshot_relative),
        "snapshotHash": hashlib.sha256(snapshot_bytes).hexdigest(),
        "recordedAt": datetime.now(TAIPEI).isoformat(),
    }


def pending_reason(root, series, start, entry, refresh):
    if refresh:
        return "requested-refresh"
    if entry is None:
        return "not-recorded"
    if not matches_policy(series, entry["policyHash"]):
        return "policy-changed"
    if entry["status"] != "closed":
        return "previously-open"
    if start not in series["reportStarts"]:
        return "not-in-manifest"
    snapshot = (root / entry["snapshot"]).resolve()
    if not snapshot.is_relative_to((root / "data/reports").resolve()) or not snapshot.is_file():
        return "snapshot-missing"
    if hashlib.sha256(snapshot.read_bytes()).hexdigest() != entry["snapshotHash"]:
        return "snapshot-changed"
    try:
        if artifact_hash(root, start) != entry["artifactHash"]:
            return "artifact-changed"
    except FileNotFoundError:
        return "artifact-missing"
    return None


def plan(root, series, entries, today, through=None, from_date=None, include_open=False, refresh=False):
    today_day = day(today)
    cutoff = day(through) if through else (today_day if include_open else sunday(today_day) - timedelta(days=1))
    if cutoff > today_day:
        raise ValueError("不能指定未來的截止日期")
    if cutoff >= sunday(today_day) and not include_open:
        raise ValueError("截止日期包含未結束週；請加 --include-open，或指定已結束的週六")
    collection = day(series["collectionStart"])
    first = sunday(collection)
    begin = max(first, sunday(day(from_date))) if from_date else first
    if from_date and day(from_date) > cutoff:
        raise ValueError("開始日期不可晚於截止日期")
    weeks, skipped = [], []
    contiguous = None
    contiguous_broken = False
    cursor = first
    while cursor <= cutoff and cutoff >= collection:
        start = str(cursor)
        reason = pending_reason(root, series, start, entries.get(start), refresh and cursor >= begin)
        if reason is None and not contiguous_broken:
            contiguous = start
        else:
            contiguous_broken = True
        if cursor >= begin:
            if reason:
                weeks.append({"start": start, "endExclusive": str(cursor + WEEK),
                              "coverageStart": str(max(cursor, collection)),
                              "coverageThrough": str(cursor + WEEK - timedelta(days=1) if cursor + WEEK <= today_day
                                                     else min(cursor + WEEK - timedelta(days=1), cutoff)),
                              "periodState": "closed" if cursor + WEEK <= today_day else "open", "reason": reason})
            else:
                skipped.append(start)
        cursor += WEEK
    return {"collectionStart": str(collection), "through": str(cutoff), "timezone": "Asia/Taipei",
            "lastContiguousClosedWeek": contiguous, "weeks": weeks, "skipped": skipped}


def load_state(path, series):
    if not path.exists():
        return {"schemaVersion": 1, "collectionStart": series["collectionStart"], "weeks": {}}
    state = read_json(path)
    if state.get("schemaVersion") != 1 or state.get("collectionStart") != series["collectionStart"]:
        raise ValueError("進度 schema 或系列起點不同；請保留舊檔並建立另一份進度檔")
    return state


def save_state(path, state):
    path.parent.mkdir(parents=True, exist_ok=True)
    state["updatedAt"] = datetime.now(TAIPEI).isoformat()
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", dir=path.parent, delete=False) as handle:
            temporary = Path(handle.name)
            json.dump(state, handle, indent=2, ensure_ascii=False)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    finally:
        if temporary and temporary.exists():
            temporary.unlink()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, default=Path.cwd())
    parser.add_argument("--state", type=Path, default=STATE)
    sub = parser.add_subparsers(dest="command", required=True)
    planner = sub.add_parser("plan", help="唯讀決定本次週次；預設補到最近結束的週六")
    planner.add_argument("--through")
    planner.add_argument("--from", dest="from_date")
    planner.add_argument("--include-open", action="store_true")
    planner.add_argument("--refresh", action="store_true")
    for name in ("bootstrap", "record"):
        writer = sub.add_parser(name)
        writer.add_argument("--snapshot", type=Path, required=True)
        if name == "record":
            writer.add_argument("--week", required=True)
    args = parser.parse_args()
    root = args.repo.resolve()
    series = read_json(root / CONTENT / "series.json")
    state_path = args.state if args.state.is_absolute() else root / args.state
    if not state_path.resolve().is_relative_to((root / "data/reports").resolve()):
        raise ValueError("進度檔必須放在私人 data/reports/ 內")
    if args.command == "plan":
        state = load_state(state_path, series)
        result = plan(root, series, state["weeks"], str(datetime.now(TAIPEI).date()), args.through,
                      args.from_date, args.include_open, args.refresh)
    else:
        # Fail rather than race another writer; stale locks can be inspected after interruption.
        state_path.parent.mkdir(parents=True, exist_ok=True)
        lock = state_path.with_suffix(".lock")
        lock.mkdir()
        try:
            state = load_state(state_path, series)
            subprocess.run(["node", "scripts/check-weekly-insights.mjs"], cwd=root / "apps/showcase",
                           check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            snapshot = args.snapshot if args.snapshot.is_absolute() else root / args.snapshot
            starts = [args.week] if args.command == "record" else series["reportStarts"]
            recorded = []
            for start in starts:
                day(start)
                if args.command == "bootstrap" and start in state["weeks"]:
                    continue
                report = read_json(root / CONTENT / start / "report.json")
                if args.command == "bootstrap" and report.get("published") is not True:
                    continue
                state["weeks"][start] = checkpoint(root, series, start, snapshot)
                recorded.append(start)
            save_state(state_path, state)
            result = {"state": str(state_path), "recorded": recorded}
        finally:
            lock.rmdir()
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    try:
        main()
    except (ValueError, KeyError, OSError, subprocess.CalledProcessError) as error:
        detail = error.stderr if isinstance(error, subprocess.CalledProcessError) else str(error)
        raise SystemExit(f"週報進度操作失敗：{detail}") from error
