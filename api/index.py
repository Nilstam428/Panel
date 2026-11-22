"""Vercel serverless entrypoint for the FastAPI application."""

import sys
from pathlib import Path

# The FastAPI package lives in server/app; make `app` importable from this
# root-level function entrypoint.
SERVER_DIR = Path(__file__).resolve().parents[1] / "server"
sys.path.insert(0, str(SERVER_DIR))

from app.main import app  # noqa: E402

