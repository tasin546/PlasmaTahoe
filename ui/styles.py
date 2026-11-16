#!/usr/bin/env python3
"""
PlasmaTahoe-Engine: UI Theme & Liquid Glass Stylesheet
Provides macOS Tahoe-inspired frosted glass styling for PyQt6 components.
"""

def get_liquid_glass_stylesheet(dark_mode: bool = True) -> str:
    """Return the complete Liquid Glass QSS stylesheet."""
    if dark_mode:
        bg_main = "#14161E"
        card_bg = "rgba(28, 32, 44, 0.72)"
        card_border = "rgba(255, 255, 255, 0.10)"
        card_hover = "rgba(38, 44, 60, 0.85)"
        text_primary = "#FFFFFF"
        text_secondary = "#A0A6B8"
        accent = "#0A84FF"
        accent_hover = "#409CFF"
        accent_pressed = "#0066D6"
        console_bg = "#0B0D13"
        console_text = "#70D6FF"
        input_bg = "rgba(20, 22, 30, 0.6)"
        tab_bg = "rgba(255, 255, 255, 0.04)"
        tab_active_bg = "rgba(10, 132, 255, 0.2)"
        sidebar_bg = "#0D0F15"
    else:
        bg_main = "#F2F4F8"
        card_bg = "rgba(255, 255, 255, 0.80)"
        card_border = "rgba(0, 0, 0, 0.08)"
        card_hover = "rgba(255, 255, 255, 0.95)"
        text_primary = "#1D1D1F"
        text_secondary = "#6E6E73"
        accent = "#007AFF"
        accent_hover = "#1A8CFF"
        accent_pressed = "#0056B3"
        console_bg = "#181A20"
        console_text = "#A3E635"
        input_bg = "#FFFFFF"
        tab_bg = "rgba(0, 0, 0, 0.04)"
        tab_active_bg = "rgba(0, 122, 255, 0.12)"
        sidebar_bg = "#E9ECF2"

    return f"""
    QMainWindow, QDialog {{
        background-color: {bg_main};
        font-family: -apple-system, BlinkMacSystemFont, "SF Pro Display", "Inter", "Segoe UI", Roboto, sans-serif;
        color: {text_primary};
    }}

    QWidget#CentralWidget {{
        background-color: {bg_main};
    }}

    /* Card Panels */
    QFrame.glass-card {{
        background-color: {card_bg};
        border: 1px solid {card_border};
        border-radius: 14px;
        padding: 16px;
    }}

    QFrame.glass-card:hover {{
        background-color: {card_hover};
        border: 1px solid {accent};
    }}

    /* Badges */
    QLabel.badge {{
        background-color: {tab_active_bg};
        color: {accent};
        font-weight: bold;
        font-size: 11px;
        padding: 4px 10px;
        border-radius: 10px;
        border: 1px solid {card_border};
    }}

    QLabel.badge-success {{
        background-color: rgba(52, 199, 89, 0.18);
        color: #34C759;
        font-weight: bold;
        font-size: 11px;
        padding: 4px 10px;
        border-radius: 10px;
    }}

    QLabel.badge-warning {{
        background-color: rgba(255, 159, 10, 0.18);
        color: #FF9F0A;
        font-weight: bold;
        font-size: 11px;
        padding: 4px 10px;
        border-radius: 10px;
    }}

    /* Headers */
    QLabel.title {{
        font-size: 24px;
        font-weight: 700;
        color: {text_primary};
        letter-spacing: -0.5px;
    }}

    QLabel.subtitle {{
        font-size: 13px;
        color: {text_secondary};
        line-height: 1.4;
    }}

    QLabel.section-header {{
        font-size: 15px;
        font-weight: 600;
        color: {text_primary};
        margin-top: 8px;
        margin-bottom: 4px;
    }}

    /* Buttons */
    QPushButton {{
        background-color: {card_bg};
        color: {text_primary};
        border: 1px solid {card_border};
        border-radius: 9px;
        padding: 8px 18px;
        font-size: 13px;
        font-weight: 500;
        min-height: 20px;
    }}

    QPushButton:hover {{
        background-color: {card_hover};
        border: 1px solid {accent};
    }}

    QPushButton:pressed {{
        background-color: {tab_active_bg};
    }}

    QPushButton.primary {{
        background-color: {accent};
        color: #FFFFFF;
        border: none;
        font-weight: 600;
    }}

    QPushButton.primary:hover {{
        background-color: {accent_hover};
    }}

    QPushButton.primary:pressed {{
        background-color: {accent_pressed};
    }}

    QPushButton.danger {{
        background-color: rgba(255, 69, 58, 0.15);
        color: #FF453A;
        border: 1px solid rgba(255, 69, 58, 0.3);
    }}

    QPushButton.danger:hover {{
        background-color: #FF453A;
        color: #FFFFFF;
    }}

    /* Checkboxes */
    QCheckBox {{
        font-size: 13px;
        color: {text_primary};
        spacing: 10px;
    }}

    QCheckBox::indicator {{
        width: 18px;
        height: 18px;
        border-radius: 5px;
        border: 1px solid {card_border};
        background-color: {input_bg};
    }}

    QCheckBox::indicator:checked {{
        background-color: {accent};
        border: 1px solid {accent};
        image: none;
    }}

    /* Radio Buttons */
    QRadioButton {{
        font-size: 13px;
        color: {text_primary};
        spacing: 8px;
    }}

    QRadioButton::indicator {{
        width: 18px;
        height: 18px;
        border-radius: 9px;
        border: 1px solid {card_border};
        background-color: {input_bg};
    }}

    QRadioButton::indicator:checked {{
        background-color: {accent};
        border: 4px solid {bg_main};
    }}

    /* Sliders */
    QSlider::groove:horizontal {{
        height: 6px;
        background: {tab_bg};
        border-radius: 3px;
    }}

    QSlider::sub-page:horizontal {{
        background: {accent};
        border-radius: 3px;
    }}

    QSlider::handle:horizontal {{
        background: #FFFFFF;
        border: 1px solid {card_border};
        width: 18px;
        margin-top: -6px;
        margin-bottom: -6px;
        border-radius: 9px;
    }}

    /* Progress Bar */
    QProgressBar {{
        background-color: {tab_bg};
        border: 1px solid {card_border};
        border-radius: 8px;
        height: 14px;
        text-align: center;
        color: {text_primary};
        font-size: 10px;
        font-weight: bold;
    }}

    QProgressBar::chunk {{
        background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 {accent}, stop:1 #5AC8FA);
        border-radius: 7px;
    }}

    /* Console View */
    QPlainTextEdit.console {{
        background-color: {console_bg};
        color: {console_text};
        font-family: "JetBrains Mono", "Fira Code", "Cascadia Code", "Consolas", monospace;
        font-size: 12px;
        border: 1px solid {card_border};
        border-radius: 10px;
        padding: 10px;
        selection-background-color: {accent};
    }}

    /* Scrollbars */
    QScrollBar:vertical {{
        background: transparent;
        width: 8px;
        margin: 0;
    }}

    QScrollBar::handle:vertical {{
        background: {card_border};
        min-height: 24px;
        border-radius: 4px;
    }}

    QScrollBar::handle:vertical:hover {{
        background: {text_secondary};
    }}

    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
        height: 0;
    }}

    /* Tab Widget & Navigation Sidebar */
    QListWidget#NavigationList {{
        background-color: {sidebar_bg};
        border: none;
        border-right: 1px solid {card_border};
        padding: 14px 8px;
        outline: none;
    }}

    QListWidget#NavigationList::item {{
        height: 42px;
        padding-left: 14px;
        border-radius: 8px;
        font-size: 13px;
        font-weight: 500;
        color: {text_secondary};
        margin-bottom: 4px;
    }}

    QListWidget#NavigationList::item:selected {{
        background-color: {tab_active_bg};
        color: {accent};
        font-weight: 600;
    }}

    QListWidget#NavigationList::item:hover:!selected {{
        background-color: {tab_bg};
        color: {text_primary};
    }}

    /* Backups List View */
    QListWidget.backup-list {{
        background-color: {card_bg};
        border: 1px solid {card_border};
        border-radius: 10px;
        padding: 8px;
    }}

    QListWidget.backup-list::item {{
        padding: 12px;
        border-bottom: 1px solid {card_border};
        border-radius: 6px;
    }}

    QListWidget.backup-list::item:selected {{
        background-color: {tab_active_bg};
        color: {accent};
    }}
    """
