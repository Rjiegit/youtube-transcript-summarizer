import os
from datetime import datetime
from config import Config
from transcriber import Transcriber
from summarizer import Summarizer
from file_manager import FileManager
from summary_storage import SummaryStorage
from processor import Processor
from logger import logger

class Main:
    """
    Main class that orchestrates the application workflow.
    Uses dependency injection to receive components and focuses on orchestration only.
    """

    def __init__(self, config=None, transcriber=None, summarizer=None, file_manager=None, summary_storage=None, processor=None):
        """
        Initialize the Main class with dependencies.

        Args:
            config (Config, optional): Configuration object. If not provided, a new one will be created.
            transcriber (TranscriberInterface, optional): Transcriber to use. If not provided, a new one will be created.
            summarizer (SummarizerInterface, optional): Summarizer to use. If not provided, a new one will be created.
            file_manager (FileManagerInterface, optional): File manager to use. If not provided, a new one will be created.
            summary_storage (SummaryStorageInterface, optional): Summary storage to use. If not provided, a new one will be created.
            processor (Processor, optional): Processor to use. If not provided, a new one will be created.
        """
        # Create or use provided configuration
        self.config = config if config else Config()

        # Validate configuration
        self.config.validate()

        # Create or use provided components
        self.transcriber = transcriber if transcriber else Transcriber(config=self.config)
        self.summarizer = summarizer if summarizer else Summarizer(config=self.config)
        self.file_manager = file_manager if file_manager else FileManager(config=self.config)
        self.summary_storage = summary_storage if summary_storage else SummaryStorage(config=self.config)

        # Create or use provided processor
        self.processor = processor if processor else Processor(
            transcriber=self.transcriber,
            summarizer=self.summarizer,
            file_manager=self.file_manager,
            summary_storage=self.summary_storage,
            config=self.config
        )

    def run(self):
        """
        Run the application workflow.
        """
        # Record start time
        start_time = datetime.now(self.config.timezone)
        logger.info(f"Process started at: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")

        # Get files to process
        files_to_process = self.file_manager.get_files_to_process(self.config.file_patterns)

        logger.info(f"Total files to process: {len(files_to_process)}")

        # Process each file
        for index, file_path in enumerate(files_to_process, start=1):
            logger.info(f"Processing file {index}/{len(files_to_process)}: {file_path}")
            self.processor.process_file(file_path)

        # Clean up Zone.Identifier files
        self.file_manager.delete_zone_identifier_files()

        # Record end time and log summary
        end_time = datetime.now(self.config.timezone)
        logger.info(f"Process ended at: {end_time.strftime('%Y-%m-%d %H:%M:%S')}")
        logger.info(f"Total time: {(end_time - start_time).total_seconds()} seconds")

if __name__ == "__main__":
    try:
        # Create and run the application
        app = Main()
        app.run()
    except Exception as e:
        logger.error(f"Error: {e}")
    finally:
        logger.info("Process completed.")
        os._exit(0)
