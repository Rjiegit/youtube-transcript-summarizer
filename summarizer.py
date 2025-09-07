import os
from openai import OpenAI
import requests
from dotenv import load_dotenv
import google.generativeai as genai
import prompt
from logger import logger
import time
import random

try:
    import streamlit as st
except ImportError:
    st = None

try:
    from test_sample_manager import TestSampleManager
except ImportError:
    TestSampleManager = None

load_dotenv()


class Summarizer:
    def __init__(self):
        self.openai_api_key = os.getenv("OPENAI_API_KEY")
        self.google_gemini_api_key = os.getenv("GOOGLE_GEMINI_API_KEY")

    def summarize(self, title, text):
        # 檢查是否為測試模式
        if self._is_test_mode(text):
            return self._mock_summarize(title, text)

        return self.summarize_with_google_gemini(title, text)

    def _is_test_mode(self, text):
        """檢測是否為測試模式"""
        # 方法 1: 檢查 Streamlit session_state
        if (
            st
            and hasattr(st, "session_state")
            and st.session_state.get("test_mode", False)
        ):
            return True

        # 方法 2: 檢查文字內容中的測試標記
        if text and any(
            marker in text for marker in ["[測試模式]", "[mock]", "[test]"]
        ):
            return True

        return False

    def _mock_summarize(self, title, text):
        """模擬摘要過程"""
        logger.info("[測試模式] 模擬文字摘要...")

        # 檢查 TestSampleManager 是否可用
        if TestSampleManager is None:
            logger.warning("[測試模式] TestSampleManager 不可用，使用基本模擬")
            time.sleep(random.uniform(0.8, 1.5))
            return f"[測試模式摘要] {title}\n\n這是一個模擬的摘要內容，用於測試目的。"

        # 模擬處理時間
        time.sleep(random.uniform(0.8, 1.5))

        # 檢查是否要模擬錯誤
        sample_manager = TestSampleManager()
        if sample_manager.simulate_error():
            error_msg = sample_manager.get_random_error_message()
            logger.error(f"[測試模式] 模擬摘要錯誤: {error_msg}")
            raise Exception(f"[測試模式] {error_msg}")

        # 根據標題或轉錄文字內容選擇對應樣本摘要
        summary = sample_manager.get_mock_summary(title, text)

        logger.info(f"[測試模式] 模擬摘要完成，摘要長度: {len(summary)} 字元")
        logger.info(f"[測試模式] 摘要來源: {title}")

        return summary

    def get_prompt(self, title, text):
        return prompt.PROMPT_3.format(title=title, text=text)

    def summarize_with_openai(self, title, text):
        if not self.openai_api_key:
            raise ValueError("API key is not set. Please add it to the .env file.")

        client = OpenAI(api_key=self.openai_api_key)
        prompt_text = self.get_prompt(title=title, text=text)
        resp = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": prompt_text},
            ],
            temperature=0.5,
        )
        return resp.choices[0].message.content.strip()

    def summarize_with_google_gemini(self, title, text):
        if not self.google_gemini_api_key:
            raise ValueError("API key is not set. Please add it to the .env file.")

        genai.configure(api_key=self.google_gemini_api_key)

        model = genai.GenerativeModel("gemini-2.0-flash")
        response = model.generate_content(self.get_prompt(title=title, text=text))

        return response.text

    def summarize_with_ollama(self, title, text):
        logger.info(f"Summarize with Ollama...")
        url = "http://host.docker.internal:11434/api/generate"
        headers = {"Content-Type": "application/json"}
        data = {
            "model": "llama3.2",
            "prompt": self.get_prompt(title=title, text=text),
            "stream": False,
        }
        response = requests.post(url, headers=headers, json=data)
        if response.status_code == 200:
            summary = response.json().get("response", "")
            return summary
        else:
            logger.error(
                f"Error from Ollama API: {response.status_code} {response.text}"
            )
            raise Exception(
                f"Error from Ollama API: {response.status_code} {response.text}"
            )
