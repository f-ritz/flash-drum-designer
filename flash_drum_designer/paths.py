"""Application path helpers for development and frozen Windows builds."""

from __future__ import annotations

import sys
from datetime import datetime
from pathlib import Path

ICON_FILENAME = "icon.ico"
ASSETS_DIRNAME = "assets"


def is_frozen() -> bool:
    """Return True when running as a PyInstaller-built executable."""
    return getattr(sys, "frozen", False)


def get_app_dir() -> Path:
    """
    Directory used for user-facing output files.

    When frozen, this is the folder containing the .exe.
    In development, this is the project root.
    """
    if is_frozen():
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parent.parent


def get_bundle_dir() -> Path:
    """Directory containing bundled application resources."""
    if is_frozen():
        return Path(getattr(sys, "_MEIPASS"))
    return get_app_dir()


def get_icon_path() -> Path | None:
    """
    Resolve the application icon path.

    Drop your custom icon at assets/icon.ico before building the EXE.
    """
    candidates = (
        get_bundle_dir() / ASSETS_DIRNAME / ICON_FILENAME,
        get_app_dir() / ASSETS_DIRNAME / ICON_FILENAME,
        get_app_dir() / ICON_FILENAME,
    )
    for candidate in candidates:
        if candidate.is_file():
            return candidate
    return None


def build_pdf_filename(orientation: str, *, timestamp: datetime | None = None) -> str:
    """Build a timestamped PDF filename for a sizing report."""
    stamp = (timestamp or datetime.now()).strftime("%Y%m%d_%H%M%S")
    return f"flash_drum_{orientation}_sizing_{stamp}.pdf"


def build_default_pdf_path(orientation: str, *, timestamp: datetime | None = None) -> Path:
    """Return the default PDF output path next to the app/EXE."""
    return get_app_dir() / build_pdf_filename(orientation, timestamp=timestamp)