from pytubefix import YouTube
from pytubefix.cli import on_progress
import whisper
from faster_whisper import WhisperModel
import os
import openai
import requests
from dotenv import load_dotenv
from datetime import datetime
import pytz
import argparse

load_dotenv()

def download_youtube_video(url, output_path="data"):
    print(f"Download youtube video...")
    yt = YouTube(url, on_progress_callback = on_progress)
    video = yt.streams.filter(only_audio=True).first()
    if not os.path.exists(output_path):
        os.makedirs(output_path)
    video_path = video.download(output_path=output_path)
    
    return {
        "path": video_path,
        "title": yt.title
    }

def transcribe_audio(file_path, model="base"):
    print(f"Transcript audio...")
    # 加載 Whisper 模型
    whisper_model = whisper.load_model(model)
    # 進行轉錄
    result = whisper_model.transcribe(file_path, verbose=True, fp16=False)
    return result['text']

def transcribe_audio_with_faster_whisper(file_path, model="base"):
    print(f"Transcript audio...")
    # 加載 Whisper 模型
    model_size = model
    whisper_model = WhisperModel(model_size, compute_type="float32")
    # 進行轉錄
    segments, info = whisper_model.transcribe(file_path)
    
    transcript_text = ""
    for segment in segments:
        print("[%.2fs -> %.2fs] %s" % (segment.start, segment.end, segment.text))
        transcript_text += segment.text
    return transcript_text

def save_transcription(text, output_file="transcription.txt"):
    print(f"Save transcription...")
    with open(output_file, "w", encoding="utf-8") as file:
        file.write(text)
    print(f"Transcription saved to {output_file}")
    
def summarize_transcription_with_openai(text):
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("API key is not set. Please add it to the .env file.")
    
    openai.api_key = api_key

    response = openai.Completion.create(
        engine="gpt-4o-mini",
        prompt=f"請將這份逐字稿轉換成一篇淺顯易懂、重點突出、流程清晰的文章，包含內容分析、關鍵資訊提取、重新撰寫、強調重點、完善結構，並在適當位置添加重點提示，確保整個脈絡清晰有條理。===\n\n{text}",
        max_tokens=500,
        temperature=0.5
    )

    summary = response.choices[0].text.strip()
    return summary

def summarize_transcription_with_google_gemini(text):
    api_key = os.getenv("GOOGLE_GEMINI_API_KEY")
    if not api_key:
        raise ValueError("API key is not set. Please add it to the .env file.")
    
    url = "https://gemini.googleapis.com/v1/summarize"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    data = {
        "text": text,
        "max_length": 500
    }
    response = requests.post(url, headers=headers, json=data)
    if response.status_code == 200:
        summary = response.json().get("summary", "")
        return summary
    else:
        raise Exception(f"Error from Google Gemini API: {response.status_code} {response.text}")
    
def summarize_transcription_with_ollama(text):
    print(f"Summarize with Ollama...")
    url = "http://host.docker.internal:11434/api/generate"
    headers = {
        "Content-Type": "application/json"
    }
    data = {
        "model": "llama3.2",
        "prompt": f"請將這份逐字稿轉換成一篇淺顯易懂、重點突出、流程清晰的文章，包含內容分析、關鍵資訊提取、重新撰寫、強調重點、完善結構，並在適當位置添加重點提示，確保整個脈絡清晰有條理。請使用繁體中文作為輸出。===\n\n{text}",
        "stream": False
    }
    response = requests.post(url, headers=headers, json=data)
    if response.status_code == 200:
        summary = response.json().get("response", "")
        print(f"{summary}")
        return summary
    else:
        raise Exception(f"Error from Ollama API: {response.status_code} {response.text}")


def summarize_and_save_transcription(text, output_file="article_summary.txt"):
    summarized_text = summarize_transcription_with_ollama(text)
    with open(output_file, "w", encoding="utf-8") as file:
        file.write(summarized_text)
    print(f"Summarized article saved to {output_file}")


try:
    # 設定台灣時區
    taiwan_timezone = pytz.timezone("Asia/Taipei")
    
    # 開始時間
    start_time = datetime.now(taiwan_timezone)
    print(f"程式開始於：{start_time.strftime('%Y-%m-%d %H:%M:%S')}")
    
    
    # 設定 argparse 來接收命令列引數
    parser = argparse.ArgumentParser(description="下載 YouTube 影片並轉錄字幕")
    parser.add_argument("youtube_url", type=str, help="YouTube 影片網址")
    args = parser.parse_args()
    
    # 主流程
    youtube_url = args.youtube_url
    download_result = download_youtube_video(youtube_url)
    file_path = download_result["path"]
    file_title = download_result["title"]
    
    transcription_text = transcribe_audio_with_faster_whisper(file_path)
    
    save_transcription(transcription_text, output_file=f"data/{file_title}.txt")
    summarize_and_save_transcription(transcription_text, output_file=f"data/summarized_{file_title}_summary.md")
    
    # 結束時間
    end_time = datetime.now(taiwan_timezone)
    
    print(f"程式結束於：{end_time.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"總耗時：{(end_time - start_time).total_seconds()} 秒")
    
except Exception as e:
    print(f"Error: {e}")
