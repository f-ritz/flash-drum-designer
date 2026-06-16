"""Smoke tests for the Windows 10 desktop theme."""

from __future__ import annotations

import pytest
from PySide6.QtWidgets import QApplication

from flash_drum_designer.theme import WINDOWS10_STYLESHEET, apply_windows10_theme


@pytest.fixture(scope="module")
def qapp() -> QApplication:
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app


def test_apply_windows10_theme_sets_font_and_stylesheet(qapp: QApplication) -> None:
    apply_windows10_theme(qapp)
    assert qapp.font().family() == "Segoe UI"
    assert qapp.font().pointSize() == 9
    assert qapp.styleSheet() == WINDOWS10_STYLESHEET