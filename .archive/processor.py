from datetime import datetime
from logger import logger

class Processor:
    """
    Processor class that handles the processing of individual files.
    Extracts the processing logic from the Main class to reduce its responsibilities.
    """
    
    def __init__(self, transcriber, summarizer, file_manager, summary_storage, config=None):
        """
        Initialize the processor with dependencies.
        
        Args:
            transcriber (TranscriberInterface): The transcriber to use.
            summarizer (SummarizerInterface): The summarizer to use.
            file_manager (FileManagerInterface): The file manager to use.
            summary_storage (SummaryStorageInterface): The summary storage to use.
            config (Config, optional): Configuration object.
        """
        self.transcriber = transcriber
        self.summarizer = summarizer
        self.file_manager = file_manager
        self.summary_storage = summary_storage
        self.config = config
    
    def process_file(self, file_path):
        """
        Process a single file: transcribe, summarize, save, and clean up.
        
        Args:
            file_path (str): Path to the file to process.
            
        Returns:
            bool: True if processing was successful, False otherwise.
        """
        try:
            start_time = datetime.now()  # Record start time
            file_title = self._extract_title(file_path)
            logger.info(f"Processing file: {file_title}")
            
            # Transcribe the file
            transcription_text = self.transcriber.transcribe(file_path)
            
            # Generate timestamp for the output file
            datetime_now = datetime.now().strftime('%Y%m%d%H%M%S')
            
            # Summarize the transcription
            summarized_text = self.summarizer.summarize(file_title, transcription_text)
            
            # Save the summary to a file
            output_file = f"_summarized/{datetime_now}_{file_title}.md"
            self.file_manager.save_text(summarized_text, output_file)
            
            # Save the summary to storage (e.g., Notion)
            self.summary_storage.save(
                title=file_title,
                text=summarized_text,
                model="",  # TODO: Get model information from transcriber/summarizer
                url=file_path
            )
            
            # Delete the original file
            self.file_manager.delete_file(file_path)
            
            # Record and log processing time
            end_time = datetime.now()
            processing_time = (end_time - start_time).total_seconds()
            logger.info(f"Finished processing {file_title} in {processing_time:.2f} seconds")
            
            return True
        except Exception as e:
            logger.error(f"Error processing file {file_path}: {e}")
            # Delete the file to prevent repeated processing attempts
            self.file_manager.delete_file(file_path)
            return False
    
    def _extract_title(self, file_path):
        """
        Extract the title from a file path.
        
        Args:
            file_path (str): Path to the file.
            
        Returns:
            str: The extracted title.
        """
        import os
        return os.path.splitext(os.path.basename(file_path))[0]