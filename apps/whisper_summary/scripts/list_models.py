import os
import pprint

from dotenv import load_dotenv
from google import genai


def main() -> None:
    load_dotenv()
    api_key = os.getenv("GOOGLE_GEMINI_API_KEY")
    if not api_key:
        raise ValueError("GOOGLE_GEMINI_API_KEY is not set. Please add it to the .env file.")
    with genai.Client(api_key=api_key) as client:
        for model in client.models.list():
            pprint.pprint(model)


if __name__ == "__main__":
    main()
