from dataclasses import dataclass
from enum import Enum


class Backend(str, Enum):
    GEMINI = "gemini"
    OPENAI = "openai"
    OLLAMA = "ollama"
    CODEX_CLI = "codex_cli"


class OpenAIModel(str, Enum):
    GPT_4O_MINI = "gpt-4o-mini"


class GeminiModel(str, Enum):
    GEMINI_2_5_FLASH = "gemini-2.5-flash"
    GEMINI_2_5_FLASH_LITE = "gemini-2.5-flash-lite"
    GEMINI_3_FLASH = "gemini-3-flash"
    GEMINI_3_FLASH_PREVIEW = "gemini-3-flash-preview"
    GEMINI_3_1_FLASH_LITE = "gemini-3.1-flash-lite"
    GEMINI_3_5_FLASH_LITE = "gemini-3.5-flash-lite"
    GEMINI_3_7_FLASH = "gemini-3.7-flash"


class OllamaModel(str, Enum):
    KIMI_K2_5_CLOUD = "kimi-k2.5:cloud"
    QWEN3_CODER_480B_CLOUD = "qwen3-coder:480b-cloud"


class CodexModel(str, Enum):
    GPT_6_LUNA = "gpt-6-luna"


@dataclass(frozen=True)
class ProviderSettings:
    api_key_env: str
    default_model: str


@dataclass(frozen=True)
class ModelCandidate:
    backend: Backend
    model: str
    weight: float

    @property
    def key(self) -> tuple[Backend, str]:
        return self.backend, self.model


PROVIDER_SETTINGS: dict[Backend, ProviderSettings] = {
    Backend.GEMINI: ProviderSettings(
        api_key_env="GOOGLE_GEMINI_API_KEY",
        default_model=GeminiModel.GEMINI_3_5_FLASH_LITE.value,
    ),
    Backend.OPENAI: ProviderSettings(
        api_key_env="OPENAI_API_KEY",
        default_model=OpenAIModel.GPT_4O_MINI.value,
    ),
    Backend.OLLAMA: ProviderSettings(
        api_key_env="OLLAMA_API_KEY",
        default_model=OllamaModel.KIMI_K2_5_CLOUD.value,
    ),
}

# Backward-compatible names used by the provider-specific methods.
GEMINI_MODEL = PROVIDER_SETTINGS[Backend.GEMINI].default_model
OPENAI_MODEL = PROVIDER_SETTINGS[Backend.OPENAI].default_model
OLLAMA_MODEL = PROVIDER_SETTINGS[Backend.OLLAMA].default_model
CODEX_MODEL = CodexModel.GPT_6_LUNA.value

# Default Gemini candidates total 10. Codex CLI gets 90 of the 100 total
# weight points when both Gemini and the local CLI are available.
CODEX_CLI_WEIGHT = 90

# The single source of truth for auto mode. Default weights add up to 100,
# but selection renormalizes them for eligible candidates. A credential only
# makes a provider available; models receive auto traffic only when listed here.
AUTO_MODEL_CANDIDATES: tuple[ModelCandidate, ...] = (
    ModelCandidate(
        backend=Backend.GEMINI,
        model=GeminiModel.GEMINI_3_7_FLASH.value,
        weight=0.91,
    ),
    ModelCandidate(
        backend=Backend.GEMINI,
        model=GeminiModel.GEMINI_2_5_FLASH_LITE.value,
        weight=1.82,
    ),
    ModelCandidate(
        backend=Backend.GEMINI,
        model=GeminiModel.GEMINI_2_5_FLASH.value,
        weight=0.91,
    ),
    ModelCandidate(
        backend=Backend.GEMINI,
        model=GeminiModel.GEMINI_3_FLASH_PREVIEW.value,
        weight=0.91,
    ),
    ModelCandidate(
        backend=Backend.GEMINI,
        model=GeminiModel.GEMINI_3_1_FLASH_LITE.value,
        weight=2.73,
    ),
    ModelCandidate(
        backend=Backend.GEMINI,
        model=GeminiModel.GEMINI_3_5_FLASH_LITE.value,
        weight=2.72,
    ),
    ModelCandidate(
        backend=Backend.CODEX_CLI,
        model=CODEX_MODEL,
        weight=CODEX_CLI_WEIGHT,
    ),
)
