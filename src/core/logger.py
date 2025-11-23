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


logger = Logger()
