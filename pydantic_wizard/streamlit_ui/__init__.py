"""Streamlit web UI for pydantic-wizard."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path


def launch() -> None:
    """Launch the Streamlit web interface.

    Raises:
        ImportError: If streamlit is not installed.
    """
    try:
        import streamlit  # noqa: F401
    except ImportError as e:
        raise ImportError(
            "Streamlit is required for the web UI. "
            "Install it with: pip install pydantic-wizard[web]"
        ) from e

    app_path = Path(__file__).parent / "app.py"
    subprocess.run(
        [
            sys.executable,
            "-m",
            "streamlit",
            "run",
            str(app_path),
            "--server.headless=true",
        ],
        check=False,
    )
