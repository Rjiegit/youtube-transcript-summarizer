# Call ListModels to see the list of available models and their supported methods.
import google.generativeai as genai
import os
import pprint
from dotenv import load_dotenv

load_dotenv()

google_gemini_api_key = os.getenv("GOOGLE_GEMINI_API_KEY")

genai.configure(api_key=google_gemini_api_key)

for model in genai.list_models():
    pprint.pprint(model)
