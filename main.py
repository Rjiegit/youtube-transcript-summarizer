from pytubefix import YouTube
from pytubefix.cli import on_progress
import whisper
import os

def download_youtube_video(url, output_path="downloads"):
    print(f"Download youtube video...")
    yt = YouTube(url, on_progress_callback = on_progress)
    video = yt.streams.filter(only_audio=True).first()
    if not os.path.exists(output_path):
        os.makedirs(output_path)
    video_path = video.download(output_path=output_path)
    return video_path

def transcribe_audio(file_path, model="base"):
    print(f"Transcript audio...")
    # 加載 Whisper 模型
    whisper_model = whisper.load_model(model)
    # 進行轉錄
    result = whisper_model.transcribe(file_path)
    return result['text']

def save_transcription(text, output_file="transcription.txt"):
    print(f"Save transcription...")
    with open(output_file, "w", encoding="utf-8") as file:
        file.write(text)
    print(f"Transcription saved to {output_file}")


try:
    # 主流程
    youtube_url = "https://www.youtube.com/watch?v=UcmNQTk-pY4"
    audio_file = download_youtube_video(youtube_url)
    transcription_text = transcribe_audio(audio_file)
    save_transcription(transcription_text)
except Exception as e:
    print(f"Error downloading video: {e}")
