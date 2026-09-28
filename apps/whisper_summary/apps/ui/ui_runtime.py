# ruff: noqa: E402 - streamlit needs top-level imports
from __future__ import annotations

try:  # pragma: no cover - optional for local runs
    import requests as _requests
    RequestException = _requests.RequestException
except ModuleNotFoundError:  # pragma: no cover - allow logic tests without network libs
    _requests = None

    class RequestException(Exception):
        pass

try:  # pragma: no cover - optional for local runs
    import streamlit as st
except ModuleNotFoundError:  # pragma: no cover - allow logic tests without Streamlit
    st = None

requests = _requests


def require_streamlit() -> None:
    if st is None:  # pragma: no cover - guard when Streamlit is absent in tests
        raise RuntimeError("Streamlit must be installed to run the UI.")


def require_requests() -> None:
    if requests is None:  # pragma: no cover - guard when requests is absent in tests
        raise RuntimeError("requests is required to call the API.")
