# src/main.py
# Wrapper entrypoint for Google Cloud Functions (Gen2).
# Cloud Functions expects the target callable to be importable from the source root module.

from app.main import main  # re-export
