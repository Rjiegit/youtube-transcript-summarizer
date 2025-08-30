import schedule
import time
from processing import process_pending_tasks
from logger import logger

if __name__ == "__main__":
    logger.info("Scheduler started.")
    schedule.every(5).minutes.do(process_pending_tasks)

    while True:
        schedule.run_pending()
        time.sleep(1)
