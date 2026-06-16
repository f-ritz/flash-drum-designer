"""Windows 10 visual theme for the desktop application."""

from __future__ import annotations

import sys

from PySide6.QtGui import QColor, QFont, QPalette
from PySide6.QtWidgets import QApplication

# Windows 10 system colors (Settings / legacy control panel).
WIN10_WINDOW = "#f3f3f3"
WIN10_SURFACE = "#ffffff"
WIN10_BORDER = "#7a7a7a"
WIN10_BORDER_LIGHT = "#e1e1e1"
WIN10_TEXT = "#000000"
WIN10_TEXT_MUTED = "#666666"
WIN10_ACCENT = "#0078d4"
WIN10_ACCENT_HOVER = "#106ebe"
WIN10_ACCENT_PRESSED = "#005a9e"
WIN10_BUTTON_FACE = "#e1e1e1"
WIN10_BUTTON_BORDER = "#adadad"
WIN10_FOCUS = "#0078d4"
WIN10_INFO = "#005a9e"
WIN10_DISABLED_TEXT = "#a0a0a0"
WIN10_DISABLED_BG = "#f0f0f0"

WINDOWS10_STYLESHEET = f"""
QMainWindow {{
    background-color: {WIN10_WINDOW};
}}

QScrollArea {{
    border: none;
    background-color: {WIN10_WINDOW};
}}

QScrollArea > QWidget > QWidget {{
    background-color: {WIN10_WINDOW};
}}

QFrame#headerSeparator {{
    background-color: {WIN10_BORDER_LIGHT};
    max-height: 1px;
    min-height: 1px;
    border: none;
    margin-top: 4px;
    margin-bottom: 4px;
}}

QLabel#titleLabel {{
    color: {WIN10_TEXT};
    font-family: "Segoe UI Light", "Segoe UI", sans-serif;
    font-size: 22pt;
    font-weight: 300;
    padding-bottom: 2px;
}}

QLabel#subtitleLabel,
QLabel#exampleInfoLabel {{
    color: {WIN10_TEXT_MUTED};
    font-size: 9pt;
    line-height: 1.35;
}}

QLabel#kFactorPreview {{
    color: {WIN10_INFO};
    font-size: 9pt;
    padding: 8px 10px;
    background-color: #f5f9fd;
    border: 1px solid #cce4f7;
    border-radius: 2px;
}}

QGroupBox {{
    background-color: {WIN10_SURFACE};
    border: 1px solid {WIN10_BORDER_LIGHT};
    border-radius: 2px;
    margin-top: 16px;
    padding: 16px 12px 12px 12px;
    font-weight: 600;
}}

QGroupBox::title {{
    subcontrol-origin: margin;
    subcontrol-position: top left;
    left: 12px;
    padding: 0 4px;
    color: {WIN10_TEXT};
}}

QLineEdit,
QComboBox,
QDoubleSpinBox,
QSpinBox,
QTextEdit {{
    background-color: {WIN10_SURFACE};
    color: {WIN10_TEXT};
    border: 1px solid {WIN10_BORDER};
    border-radius: 2px;
    padding: 4px 8px;
    min-height: 22px;
    selection-background-color: {WIN10_ACCENT};
    selection-color: #ffffff;
}}

QLineEdit:disabled,
QComboBox:disabled,
QDoubleSpinBox:disabled,
QSpinBox:disabled {{
    color: {WIN10_DISABLED_TEXT};
    background-color: {WIN10_DISABLED_BG};
    border-color: {WIN10_BORDER_LIGHT};
}}

QComboBox::drop-down {{
    subcontrol-origin: padding;
    subcontrol-position: top right;
    width: 20px;
    border-left: 1px solid {WIN10_BORDER_LIGHT};
    background-color: {WIN10_BUTTON_FACE};
}}

QComboBox::down-arrow {{
    width: 0;
    height: 0;
    border-left: 4px solid transparent;
    border-right: 4px solid transparent;
    border-top: 5px solid {WIN10_TEXT};
    margin-right: 6px;
}}

QComboBox QAbstractItemView {{
    background-color: {WIN10_SURFACE};
    border: 1px solid {WIN10_BORDER};
    selection-background-color: {WIN10_ACCENT};
    selection-color: #ffffff;
    outline: none;
}}

QLineEdit:focus,
QComboBox:focus,
QDoubleSpinBox:focus,
QSpinBox:focus,
QTextEdit:focus {{
    border: 1px solid {WIN10_FOCUS};
}}

QTextEdit {{
    font-family: "Consolas", "Courier New", monospace;
    font-size: 9pt;
}}

QCheckBox {{
    spacing: 8px;
    color: {WIN10_TEXT};
}}

QCheckBox::indicator {{
    width: 18px;
    height: 18px;
    border: 1px solid {WIN10_BORDER};
    border-radius: 2px;
    background-color: {WIN10_SURFACE};
}}

QCheckBox::indicator:hover {{
    border-color: {WIN10_ACCENT};
}}

QCheckBox::indicator:checked {{
    background-color: {WIN10_ACCENT};
    border-color: {WIN10_ACCENT};
    image: url(data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHdpZHRoPSIxMiIgaGVpZ2h0PSIxMiIgdmlld0JveD0iMCAwIDEyIDEyIj48cGF0aCBmaWxsPSIjZmZmIiBkPSJNMTAgM0w0LjUgOC41IDIgNiIvPjwvc3ZnPg==);
}}

QScrollBar:vertical {{
    background: {WIN10_WINDOW};
    width: 12px;
    margin: 0;
}}

QScrollBar::handle:vertical {{
    background: #cdcdcd;
    min-height: 24px;
    border-radius: 6px;
    margin: 2px;
}}

QScrollBar::handle:vertical:hover {{
    background: #a6a6a6;
}}

QScrollBar::add-line:vertical,
QScrollBar::sub-line:vertical,
QScrollBar::add-page:vertical,
QScrollBar::sub-page:vertical {{
    background: none;
    height: 0;
}}

QScrollBar:horizontal {{
    background: {WIN10_WINDOW};
    height: 12px;
    margin: 0;
}}

QScrollBar::handle:horizontal {{
    background: #cdcdcd;
    min-width: 24px;
    border-radius: 6px;
    margin: 2px;
}}

QScrollBar::handle:horizontal:hover {{
    background: #a6a6a6;
}}

QScrollBar::add-line:horizontal,
QScrollBar::sub-line:horizontal,
QScrollBar::add-page:horizontal,
QScrollBar::sub-page:horizontal {{
    background: none;
    width: 0;
}}

QPushButton {{
    background-color: {WIN10_BUTTON_FACE};
    color: {WIN10_TEXT};
    border: 1px solid {WIN10_BUTTON_BORDER};
    border-radius: 2px;
    padding: 6px 20px;
    min-height: 24px;
}}

QPushButton:hover {{
    background-color: #e5f1fb;
    border-color: {WIN10_ACCENT};
}}

QPushButton:pressed {{
    background-color: #cce4f7;
}}

QPushButton:disabled {{
    color: {WIN10_DISABLED_TEXT};
    background-color: {WIN10_DISABLED_BG};
    border-color: {WIN10_BORDER_LIGHT};
}}

QPushButton:default,
QPushButton#primaryButton {{
    background-color: {WIN10_ACCENT};
    color: #ffffff;
    border: 1px solid {WIN10_ACCENT};
}}

QPushButton:default:hover,
QPushButton#primaryButton:hover {{
    background-color: {WIN10_ACCENT_HOVER};
    border-color: {WIN10_ACCENT_HOVER};
}}

QPushButton:default:pressed,
QPushButton#primaryButton:pressed {{
    background-color: {WIN10_ACCENT_PRESSED};
    border-color: {WIN10_ACCENT_PRESSED};
}}

QPushButton:default:disabled,
QPushButton#primaryButton:disabled {{
    background-color: #c8c8c8;
    border-color: #c8c8c8;
    color: #ffffff;
}}
"""


def _preferred_windows_style() -> str:
    from PySide6.QtWidgets import QStyleFactory

    styles = {name.lower(): name for name in QStyleFactory.keys()}
    for candidate in ("windowsvista", "windows11", "windows"):
        if candidate in styles:
            return styles[candidate]
    return "Fusion"


def apply_windows10_theme(app: QApplication) -> None:
    """Apply Windows 10 fonts, palette, native style (when available), and QSS."""
    if sys.platform == "win32":
        app.setStyle(_preferred_windows_style())
    else:
        app.setStyle("Fusion")

    app.setFont(QFont("Segoe UI", 9))

    palette = QPalette()
    palette.setColor(QPalette.ColorRole.Window, QColor(WIN10_WINDOW))
    palette.setColor(QPalette.ColorRole.WindowText, QColor(WIN10_TEXT))
    palette.setColor(QPalette.ColorRole.Base, QColor(WIN10_SURFACE))
    palette.setColor(QPalette.ColorRole.AlternateBase, QColor(WIN10_WINDOW))
    palette.setColor(QPalette.ColorRole.Text, QColor(WIN10_TEXT))
    palette.setColor(QPalette.ColorRole.Button, QColor(WIN10_BUTTON_FACE))
    palette.setColor(QPalette.ColorRole.ButtonText, QColor(WIN10_TEXT))
    palette.setColor(QPalette.ColorRole.Highlight, QColor(WIN10_ACCENT))
    palette.setColor(QPalette.ColorRole.HighlightedText, QColor("#ffffff"))
    palette.setColor(QPalette.ColorRole.PlaceholderText, QColor("#767676"))
    palette.setColor(QPalette.ColorRole.Mid, QColor(WIN10_BORDER_LIGHT))
    app.setPalette(palette)

    app.setStyleSheet(WINDOWS10_STYLESHEET)