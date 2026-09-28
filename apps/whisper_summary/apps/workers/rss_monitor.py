"""CLI entry for polling YouTube channel RSS feeds."""

from __future__ import annotations

import argparse

from whisper_summary.core.config import Config
from whisper_summary.services.rss.channel_monitor import RSSChannelMonitor


def main() -> None:
    parser = argparse.ArgumentParser(description="Poll YouTube RSS subscriptions.")
    parser.add_argument(
        "--once",
        action="store_true",
        help="Run a single polling cycle and exit.",
    )
    args = parser.parse_args()

    config = Config()
    if not config.rss_monitor_enabled:
        print({"enabled": False, "message": "RSS monitor is disabled."})
        return

    monitor = RSSChannelMonitor(config=config)
    if args.once:
        print([result.__dict__ for result in monitor.poll_once()])
        return
    monitor.run_forever()


if __name__ == "__main__":
    main()
