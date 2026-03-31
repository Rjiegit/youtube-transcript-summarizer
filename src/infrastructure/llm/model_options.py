from enum import Enum

from src.infrastructure.llm.weighted_selection import (
    WeightedBackendModel,
    WeightedModel,
)


class OpenAIModel(Enum):
    GPT_4O_MINI = "gpt-4o-mini"


class GeminiModel(Enum):
    GEMINI_2_5_FLASH = "gemini-2.5-flash"
    GEMINI_2_5_FLASH_LITE = "gemini-2.5-flash-lite"
    GEMINI_3_FLASH = "gemini-3-flash"
    GEMINI_3_FLASH_PREVIEW = "gemini-3-flash-preview"


class OllamaModel(Enum):
    KIMI_K2_5_CLOUD = "kimi-k2.5:cloud"
    QWEN3_CODER_480B_CLOUD = "qwen3-coder:480b-cloud"


OPENAI_MODEL = OpenAIModel.GPT_4O_MINI.value
GEMINI_MODEL = GeminiModel.GEMINI_2_5_FLASH.value
OLLAMA_MODEL = OllamaModel.KIMI_K2_5_CLOUD.value

# Weighted Gemini model selection (code-defined).
GEMINI_WEIGHTED_MODELS: list[WeightedModel] = [
    WeightedModel(model=GeminiModel.GEMINI_3_FLASH_PREVIEW.value, weight=10),
    WeightedModel(model=GeminiModel.GEMINI_2_5_FLASH.value, weight=40),
    WeightedModel(model=GeminiModel.GEMINI_2_5_FLASH_LITE.value, weight=50),
]

OLLAMA_WEIGHTED_MODELS: list[WeightedModel] = [
    WeightedModel(model=OllamaModel.KIMI_K2_5_CLOUD.value, weight=50),
    WeightedModel(model=OllamaModel.QWEN3_CODER_480B_CLOUD.value, weight=50),
]

# Weighted selection across providers for auto mode.
# `kimi-k2.5:cloud` intentionally keeps a 10% global share.
AUTO_SUMMARIZER_MODELS: list[WeightedBackendModel] = [
    WeightedBackendModel(
        backend="gemini",
        model=GeminiModel.GEMINI_3_FLASH_PREVIEW.value,
        weight=10,
    ),
    WeightedBackendModel(
        backend="gemini",
        model=GeminiModel.GEMINI_2_5_FLASH.value,
        weight=40,
    ),
    WeightedBackendModel(
        backend="gemini",
        model=GeminiModel.GEMINI_2_5_FLASH_LITE.value,
        weight=40,
    ),
    WeightedBackendModel(
        backend="ollama",
        model=OllamaModel.KIMI_K2_5_CLOUD.value,
        weight=10,
    ),
]
