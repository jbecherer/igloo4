"""
theme.py — Named UI themes for Igloo4.

Two themes are available:
  "Standard"  — system default appearance
  "Sea State" — high-contrast dark mode for bright outdoor / shipboard use:
                doubled font size, large buttons, vivid cyan accent on dark navy.

Public API
----------
apply_theme(app, name)     — apply a theme to the running QApplication
active_theme()             — return the name of the currently active theme
active_legend_fontsize()   — return the matplotlib legend font size for the active theme
"""

from __future__ import annotations

import matplotlib

# ---------------------------------------------------------------------------
# Theme definitions
# ---------------------------------------------------------------------------

THEMES: dict[str, dict] = {
    "Standard": {
        "font_family": "",          # empty → leave Qt to use the system default
        "font_size_pt": 0,          # 0 → leave Qt to use the system default
        # Minimal stylesheet: only make the Load button stand out
        "stylesheet": "QPushButton#load_btn { font-weight: bold; padding: 6px; }",
        "mpl_style": [],            # no matplotlib style override
        "mpl_font_size": 9,
        "plot_legend_fontsize": 8,
    },
    "Sea State": {
        "font_family": "Sans Serif",
        "font_size_pt": 14,         # roughly 2× the typical ~9 pt default
        "stylesheet": "",           # filled in below after QSS string is defined
        "mpl_style": ["dark_background"],
        "mpl_font_size": 14,
        "plot_legend_fontsize": 14,
    },
}

# ---------------------------------------------------------------------------
# Qt stylesheet for Sea State (dark navy + vivid cyan)
# ---------------------------------------------------------------------------
_SEA_STATE_QSS = """
/* ── Global ───────────────────────────────────────────────── */
QWidget {
    background-color: #1a1a2e;
    color: #e0e0e0;
    font-size: 14pt;
}

/* ── Buttons ──────────────────────────────────────────────── */
QPushButton, QToolButton {
    background-color: #00b4d8;
    color: #000000;
    font-weight: bold;
    border: none;
    border-radius: 6px;
    min-height: 44px;
    padding: 8px 20px;
}
QPushButton:hover, QToolButton:hover {
    background-color: #48cae4;
}
QPushButton:pressed, QToolButton:pressed {
    background-color: #0077b6;
}
QPushButton:disabled, QToolButton:disabled {
    background-color: #444466;
    color: #888888;
}

/* ── ComboBox ─────────────────────────────────────────────── */
QComboBox {
    background-color: #16213e;
    color: #e0e0e0;
    border: 1px solid #00b4d8;
    border-radius: 4px;
    padding: 6px 10px;
    min-height: 36px;
}
QComboBox QAbstractItemView {
    background-color: #16213e;
    color: #e0e0e0;
    selection-background-color: #0077b6;
}
QComboBox::drop-down {
    border: none;
}

/* ── Line edit / search box ───────────────────────────────── */
QLineEdit {
    background-color: #16213e;
    color: #e0e0e0;
    border: 1px solid #00b4d8;
    border-radius: 4px;
    padding: 6px 8px;
    min-height: 36px;
}

/* ── List / Tree views ────────────────────────────────────── */
QListWidget, QTreeView {
    background-color: #16213e;
    color: #e0e0e0;
    border: 1px solid #333355;
    alternate-background-color: #1e1e3a;
}
QListWidget::item:selected, QTreeView::item:selected {
    background-color: #0077b6;
    color: #ffffff;
}
QListWidget::item:hover, QTreeView::item:hover {
    background-color: #0d3b66;
}

/* ── Tab widget ───────────────────────────────────────────── */
QTabWidget::pane {
    border: 1px solid #333355;
    background-color: #1a1a2e;
}
QTabBar::tab {
    background-color: #16213e;
    color: #e0e0e0;
    padding: 8px 16px;
    border: 1px solid #333355;
    border-bottom: none;
    border-top-left-radius: 4px;
    border-top-right-radius: 4px;
}
QTabBar::tab:selected {
    background-color: #00b4d8;
    color: #000000;
    font-weight: bold;
}

/* ── Dock widgets ─────────────────────────────────────────── */
QDockWidget {
    color: #e0e0e0;
    font-weight: bold;
}
QDockWidget::title {
    background-color: #0d3b66;
    padding: 6px;
}

/* ── Menu bar & menus ─────────────────────────────────────── */
QMenuBar {
    background-color: #16213e;
    color: #e0e0e0;
}
QMenuBar::item:selected {
    background-color: #0077b6;
}
QMenu {
    background-color: #16213e;
    color: #e0e0e0;
    border: 1px solid #333355;
}
QMenu::item:selected {
    background-color: #0077b6;
}

/* ── Scroll bars ──────────────────────────────────────────── */
QScrollBar:vertical {
    background-color: #16213e;
    width: 12px;
}
QScrollBar::handle:vertical {
    background-color: #00b4d8;
    border-radius: 6px;
    min-height: 20px;
}
QScrollBar:horizontal {
    background-color: #16213e;
    height: 12px;
}
QScrollBar::handle:horizontal {
    background-color: #00b4d8;
    border-radius: 6px;
    min-width: 20px;
}

/* ── Status bar ───────────────────────────────────────────── */
QStatusBar {
    background-color: #0d3b66;
    color: #e0e0e0;
}

/* ── Labels ───────────────────────────────────────────────── */
QLabel {
    background-color: transparent;
    color: #e0e0e0;
}
"""

# Assign QSS string back into the Sea State theme dict
THEMES["Sea State"]["stylesheet"] = _SEA_STATE_QSS

# ---------------------------------------------------------------------------
# Module-level state
# ---------------------------------------------------------------------------

_active_theme: str = "Standard"


# ---------------------------------------------------------------------------
# Public functions
# ---------------------------------------------------------------------------

def apply_theme(app, name: str) -> None:
    """Apply the named theme to *app* (a QApplication instance).

    Also updates matplotlib rcParams so new plots respect the theme.
    """
    global _active_theme

    if name not in THEMES:
        raise ValueError(f"Unknown theme '{name}'. Available: {list(THEMES)}")

    theme = THEMES[name]
    _active_theme = name

    # --- Qt font ---
    from PyQt6.QtGui import QFont
    if theme["font_size_pt"] > 0:
        font = app.font()
        if theme["font_family"]:
            font.setFamily(theme["font_family"])
        font.setPointSize(theme["font_size_pt"])
        app.setFont(font)
    else:
        # Reset to the system default by creating a fresh default font
        app.setFont(QFont())

    # --- Qt stylesheet ---
    app.setStyleSheet(theme["stylesheet"])

    # --- matplotlib rcParams ---
    matplotlib.rcdefaults()
    for style in theme["mpl_style"]:
        try:
            matplotlib.style.use(style)
        except OSError:
            pass  # style not available; ignore

    fs = theme["mpl_font_size"]
    matplotlib.rcParams.update({
        "font.size":        fs,
        "axes.titlesize":   fs,
        "axes.labelsize":   fs,
        "xtick.labelsize":  fs - 2,
        "ytick.labelsize":  fs - 2,
        "legend.fontsize":  theme["plot_legend_fontsize"],
    })


def active_theme() -> str:
    """Return the name of the currently active theme."""
    return _active_theme


def active_legend_fontsize() -> int:
    """Return the matplotlib legend font size for the active theme."""
    return THEMES[_active_theme]["plot_legend_fontsize"]
