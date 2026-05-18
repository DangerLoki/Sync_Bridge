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
else:
    BASE_DIR = Path(__file__).resolve().parent.parent

# Ensure Jinja2 / StaticFiles can find templates and static assets
os.environ.setdefault(
    "SYNCBRIDGE_BASE_DIR", str(BASE_DIR)
)

import uvicorn  # noqa: E402  (must come after sys.path is set)


def main() -> None:
    multiprocessing.freeze_support()   # required on Windows
    uvicorn.run(
        "src.interfaces.api.app:app",
        host="0.0.0.0",
        port=8000,
        reload=False,
    )


if __name__ == "__main__":
    main()
