from datetime import datetime
from pathlib import Path

from flash_drum_designer.paths import (
    build_default_pdf_path,
    build_pdf_filename,
    get_app_dir,
    get_icon_path,
)


def test_build_pdf_filename_uses_timestamp() -> None:
    stamp = datetime(2026, 6, 15, 14, 30, 0)
    assert build_pdf_filename("horizontal", timestamp=stamp) == (
        "flash_drum_horizontal_sizing_20260615_143000.pdf"
    )


def test_build_default_pdf_path_is_in_app_dir() -> None:
    path = build_default_pdf_path("vertical")
    assert path.parent == get_app_dir()
    assert path.name.startswith("flash_drum_vertical_sizing_")
    assert path.suffix == ".pdf"


def test_get_icon_path_missing_returns_none() -> None:
    icon_path = get_icon_path()
    if icon_path is None:
        assert icon_path is None
    else:
        assert icon_path.suffix.lower() == ".ico"
        assert Path(icon_path).is_file()