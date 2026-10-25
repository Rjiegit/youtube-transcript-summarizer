import json
import traceback
from datetime import datetime
from zoneinfo import ZoneInfo


TAIPEI_TIMEZONE = ZoneInfo("Asia/Taipei")


class Logger:
    @staticmethod
    def _write(level: str, msg: object, exception: str | None = None) -> None:
        timestamp = datetime.now(TAIPEI_TIMEZONE).isoformat(timespec="milliseconds")
        record = {"timestamp": timestamp, "level": level, "message": str(msg)}
        if exception is not None:
            record["exception"] = exception
        print(json.dumps(record, ensure_ascii=False))

    @staticmethod
    def info(msg):
        Logger._write("INFO", msg)

    @staticmethod
    def warning(msg):
        Logger._write("WARNING", msg)

    @staticmethod
    def error(msg):
        Logger._write("ERROR", msg)

    @staticmethod
    def exception(msg):
        Logger._write("ERROR", msg, exception=traceback.format_exc())


logger = Logger()
