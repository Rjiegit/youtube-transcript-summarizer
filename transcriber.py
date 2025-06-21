import whisper
import os
from faster_whisper import WhisperModel
from logger import logger

class Transcriber:
    def __init__(self, model_size="base"):
        self.model_size = model_size
    
    def transcribe(self, file_path):
        return self.transcribe_with_faster_whisper(file_path)
    
    def transcribe_with_whisper(self, file_path):
        logger.info(f"Transcribing audio with Whisper...")
        whisper_model = whisper.load_model(self.model_size)
        result = whisper_model.transcribe(file_path, verbose=True, fp16=False)
        return result['text']
    
    def transcribe_with_faster_whisper(self, file_path):
        logger.info(f"Transcribing audio with Faster Whisper...")
        whisper_model = WhisperModel(
            self.model_size, 
            compute_type="int8",
            )
        segments, _ = whisper_model.transcribe(file_path)
        
        transcript_text = ""
        for segment in segments:
            # print(f"[{segment.start:.2f}s -> {segment.end:.2f}s] {segment.text}")
            transcript_text += segment.text
        return transcript_text