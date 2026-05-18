"""Standalone entry point for the SyncBridge web server (PyInstaller build)."""
import multiprocessing
import os
import sys
from pathlib import Path

# ── PyInstaller: resolve base path ───────────────────────────────────────────
# When frozen, files are extracted to sys._MEIPASS; otherwise use repo root.
if getattr(sys, "frozen", False):
    BASE_DIR = Path(sys._MEIPASS)          # type: ignore[attr-defined]
    # Work from the directory that contains the .exe / binary so that
    # relative paths (logs/, sample_data/) resolve next to the executable.
    os.chdir(Path(sys.executable).parent)
    sys.path.insert(0, str(BASE_DIR))
else:
    BASE_DIR = Path(__file__).resolve().parent.parent

os.environ.setdefault("SYNCBRIDGE_BASE_DIR", str(BASE_DIR))

# Import the app object directly — avoids uvicorn string-based module lookup
# which fails inside a frozen PyInstaller bundle.
from src.interfaces.api.app import app  # noqa: E402

import uvicorn  # noqa: E402


def main() -> None:
    multiprocessing.freeze_support()   # required on Windows
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        reload=False,
    )


if __name__ == "__main__":
    main()
