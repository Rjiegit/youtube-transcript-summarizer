from enum import Enum

from src.infrastructure.llm.gemini_model_selection import WeightedModel


class OpenAIModel(Enum):
    GPT_4O_MINI = "gpt-4o-mini"


class GeminiModel(Enum):
    GEMINI_2_5_FLASH = "gemini-2.5-flash"
    GEMINI_2_5_FLASH_LITE = "gemini-2.5-flash-lite"
    GEMINI_3_FLASH = "gemini-3-flash"
    GEMINI_3_FLASH_PREVIEW = "gemini-3-flash-preview"


class OllamaModel(Enum):
    LLAMA_3_2 = "llama3.2"


OPENAI_MODEL = OpenAIModel.GPT_4O_MINI.value
GEMINI_MODEL = GeminiModel.GEMINI_2_5_FLASH.value
OLLAMA_MODEL = OllamaModel.LLAMA_3_2.value

# Weighted Gemini model selection (code-defined).
GEMINI_WEIGHTED_MODELS: list[WeightedModel] = [
    WeightedModel(model=GeminiModel.GEMINI_3_FLASH_PREVIEW.value, weight=10),
    WeightedModel(model=GeminiModel.GEMINI_2_5_FLASH.value, weight=40),
    WeightedModel(model=GeminiModel.GEMINI_2_5_FLASH_LITE.value, weight=50),
]
