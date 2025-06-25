import os
import openai
import requests
from dotenv import load_dotenv
import google.generativeai as genai
import prompt
from logger import logger
from interfaces.summarizer_interface import SummarizerInterface

class Summarizer(SummarizerInterface):
    """
    Summarizer class that implements the SummarizerInterface.
    Provides methods to summarize text using different LLM providers.
    """

    def __init__(self, config=None):
        """
        Initialize the summarizer with configuration.

        Args:
            config (Config, optional): Configuration object. If provided, uses API keys from config.
        """
        # Load environment variables if config is not provided
        if not config:
            load_dotenv()
            self.openai_api_key = os.getenv("OPENAI_API_KEY")
            self.google_gemini_api_key = os.getenv("GOOGLE_GEMINI_API_KEY")
        else:
            self.openai_api_key = config.openai_api_key
            self.google_gemini_api_key = config.google_gemini_api_key

    def summarize(self, title, text):
        """
        Summarize the given text.

        Args:
            title (str): The title of the content to summarize.
            text (str): The text content to summarize.

        Returns:
            str: The summarized text.
        """
        return self.summarize_with_google_gemini(title, text)

    def get_prompt(self, title, text):
        """
        Get the prompt template for summarization.

        Args:
            title (str): The title of the content to summarize.
            text (str): The text content to summarize.

        Returns:
            str: The formatted prompt.
        """
        return prompt.PROMPT_2.format(title=title, text=text)

    def summarize_with_openai(self, title, text):
        """
        Summarize text using OpenAI's API.

        Args:
            title (str): The title of the content to summarize.
            text (str): The text content to summarize.

        Returns:
            str: The summarized text.

        Raises:
            ValueError: If the OpenAI API key is not set.
        """
        if not self.openai_api_key:
            raise ValueError("OpenAI API key is not set. Please add it to the .env file or configuration.")

        openai.api_key = self.openai_api_key
        response = openai.Completion.create(
            engine="gpt-4o-mini",
            prompt=self.get_prompt(title=title, text=text),
            temperature=0.5
        )
        return response.choices[0].text.strip()

    def summarize_with_google_gemini(self, title, text):
        """
        Summarize text using Google's Gemini API.

        Args:
            title (str): The title of the content to summarize.
            text (str): The text content to summarize.

        Returns:
            str: The summarized text.

        Raises:
            ValueError: If the Google Gemini API key is not set.
        """
        if not self.google_gemini_api_key:
            raise ValueError("Google Gemini API key is not set. Please add it to the .env file or configuration.")

        genai.configure(api_key=self.google_gemini_api_key)

        model = genai.GenerativeModel('gemini-2.0-flash')
        response = model.generate_content(self.get_prompt(title=title, text=text))

        return response.text

    def summarize_with_ollama(self, title, text):
        """
        Summarize text using Ollama's local API.

        Args:
            title (str): The title of the content to summarize.
            text (str): The text content to summarize.

        Returns:
            str: The summarized text.

        Raises:
            Exception: If there's an error from the Ollama API.
        """
        logger.info(f"Summarize with Ollama...")
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
            logger.error(f"Error from Ollama API: {response.status_code} {response.text}")
            raise Exception(f"Error from Ollama API: {response.status_code} {response.text}")
