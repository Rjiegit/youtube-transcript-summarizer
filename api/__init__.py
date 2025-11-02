"""HTTP API package."""

try:  # pragma: no cover - allow importing without FastAPI installed
    from .server import app
except ModuleNotFoundError:  # pragma: no cover - testing scaffold
    app = None  # type: ignore
    __all__ = []
else:
    __all__ = ["app"]
