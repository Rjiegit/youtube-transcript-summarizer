import os
import openai
import requests
from dotenv import load_dotenv

load_dotenv()

class Summarizer:
    def __init__(self):
        self.openai_api_key = os.getenv("OPENAI_API_KEY")
        self.google_gemini_api_key = os.getenv("GOOGLE_GEMINI_API_KEY")
        
    def summarize(self, text):
        return self.summarize_with_ollama(text)

    def summarize_with_openai(self, text):
        if not self.openai_api_key:
            raise ValueError("API key is not set. Please add it to the .env file.")
        
        openai.api_key = self.openai_api_key
        response = openai.Completion.create(
            engine="gpt-4o-mini",
            prompt=f"請將這份逐字稿轉換成一篇淺顯易懂、重點突出、流程清晰的文章，包含內容分析、關鍵資訊提取、重新撰寫、強調重點、完善結構，並在適當位置添加重點提示，確保整個脈絡清晰有條理。請使用繁體中文作為輸出。===\n\n{text}",
            temperature=0.5
        )
        return response.choices[0].text.strip()

    def summarize_with_google_gemini(self, text):
        if not self.google_gemini_api_key:
            raise ValueError("API key is not set. Please add it to the .env file.")
        
        url = "https://gemini.googleapis.com/v1/summarize"
        headers = {"Authorization": f"Bearer {self.google_gemini_api_key}", "Content-Type": "application/json"}
        data = {
            "text": f"請將這份逐字稿轉換成一篇淺顯易懂、重點突出、流程清晰的文章，包含內容分析、關鍵資訊提取、重新撰寫、強調重點、完善結構，並在適當位置添加重點提示，確保整個脈絡清晰有條理。請使用繁體中文作為輸出。===\n\n{text}"
        }
        
        response = requests.post(url, headers=headers, json=data)
        if response.status_code == 200:
            return response.json().get("summary", "")
        else:
            raise Exception(f"Error from Google Gemini API: {response.status_code} {response.text}")
        
    def summarize_with_ollama(self, text):
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