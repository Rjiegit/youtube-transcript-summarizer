"""Legacy compatibility wrapper for the FastAPI application.

The actual implementation lives in src.apps.api.main. Importing this module
ensures existing scripts (uvicorn, tests) continue to work without change.
"""

from src.apps.api.main import *  # noqa: F401,F403
