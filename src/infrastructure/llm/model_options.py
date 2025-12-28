from enum import Enum


class OpenAIModel(Enum):
    GPT_4O_MINI = "gpt-4o-mini"


class GeminiModel(Enum):
    GEMINI_2_5_FLASH = "gemini-2.5-flash"
    GEMINI_3_FLASH_PREVIEW = "gemini-3-flash-preview"


class OllamaModel(Enum):
    LLAMA_3_2 = "llama3.2"


OPENAI_MODEL = OpenAIModel.GPT_4O_MINI.value
GEMINI_MODEL = GeminiModel.GEMINI_2_5_FLASH.value
OLLAMA_MODEL = OllamaModel.LLAMA_3_2.value
