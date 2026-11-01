"""Entry point: `uvicorn app:app --host 0.0.0.0 --port $PORT`"""
from backend.main import app  # noqa: F401
