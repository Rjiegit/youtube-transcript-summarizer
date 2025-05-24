import os
import openai
import requests
from dotenv import load_dotenv
import google.generativeai as genai
import prompt

load_dotenv()

class Summarizer:
    def __init__(self):
        self.openai_api_key = os.getenv("OPENAI_API_KEY")
        self.google_gemini_api_key = os.getenv("GOOGLE_GEMINI_API_KEY")
        
    def summarize(self, title, text):
        return self.summarize_with_google_gemini(title, text)
    
    def get_prompt(self, title, text):
        return prompt.PROMPT_2.format(title=title, text=text)
        

    def summarize_with_openai(self, title, text):
        if not self.openai_api_key:
            raise ValueError("API key is not set. Please add it to the .env file.")
        
        openai.api_key = self.openai_api_key
        response = openai.Completion.create(
            engine="gpt-4o-mini",
            prompt=self.get_prompt(title=title, text=text),
            temperature=0.5
        )
        return response.choices[0].text.strip()

    def summarize_with_google_gemini(self, title, text):
        if not self.google_gemini_api_key:
            raise ValueError("API key is not set. Please add it to the .env file.")
        
        genai.configure(api_key=self.google_gemini_api_key)
        
        model = genai.GenerativeModel('gemini-2.0-flash')
        response = model.generate_content(self.get_prompt(title=title, text=text))
        
        return response.text
        
    def summarize_with_ollama(self, title, text):
        print(f"Summarize with Ollama...")
        url = "http://host.docker.internal:11434/api/generate"
        headers = {
            "Content-Type": "application/json"
        }
        data = {
            "model": "llama3.2",
            "prompt": self.get_prompt(title=title, text=text),
            "stream": False
        }
        response = requests.post(url, headers=headers, json=data)
        if response.status_code == 200:
            summary = response.json().get("response", "")
            return summary
        else:
            raise Exception(f"Error from Ollama API: {response.status_code} {response.text}")