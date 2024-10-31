from pytubefix import YouTube
from pytubefix.cli import on_progress
import whisper
import os
import openai
import requests
from dotenv import load_dotenv

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

def save_transcription(text, output_file="transcription.txt"):
    print(f"Save transcription...")
    with open(output_file, "w", encoding="utf-8") as file:
        file.write(text)
    print(f"Transcription saved to {output_file}")
    
def summarize_transcription_with_openai(text, api_key):
    openai.api_key = api_key

    response = openai.Completion.create(
        engine="gpt-4o-mini",
        prompt=f"請幫我將以下內容整理成一篇淺顯易懂的文章：\n\n{text}\n\n總結為：",
        max_tokens=500,
        temperature=0.5
    )

    summary = response.choices[0].text.strip()
    return summary

def summarize_transcription_with_google_gemini(text, api_key):
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


def summarize_and_save_transcription(text, api_key, output_file="summarized_article.txt"):
    summarized_text = summarize_transcription_with_google_gemini(text, api_key)
    with open(output_file, "w", encoding="utf-8") as file:
        file.write(summarized_text)
    print(f"Summarized article saved to {output_file}")


try:
    api_key = os.getenv("GOOGLE_GEMINI_API_KEY")
    if not api_key:
        raise ValueError("API key is not set. Please add it to the .env file.")
    
    # 主流程
    youtube_url = "https://www.youtube.com/watch?v=cyQwPzqJy68"
    download_result = download_youtube_video(youtube_url)
    file_path = download_result["path"]
    file_title = download_result["title"]
    
    transcription_text = transcribe_audio(file_path)
    
    save_transcription(transcription_text, output_file=f"data/{file_title}.txt")
    # summarize_and_save_transcription(transcription_text)
    
except Exception as e:
    print(f"Error: {e}")
