import traceback


class Logger:
    @staticmethod
    def info(msg):
        print(f"[INFO] {msg}")

    @staticmethod
    def warning(msg):
        print(f"[WARNING] {msg}")

    @staticmethod
    def error(msg):
        print(f"[ERROR] {msg}")

    @staticmethod
    def exception(msg):
        print(f"[ERROR] {msg}")
        traceback.print_exc()


logger = Logger()
