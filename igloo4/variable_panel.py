"""
variable_panel.py — Bottom dock panel.

Contains:
  • Favourites tab (fixed list per mode)
  • All-variables tab (searchable, populated after files are loaded)
  • Plot-mode selector (vs Time / vs Depth / vs Each Other)
  • "Add to Plot", "Clear Plot", "Export PNG" action buttons
"""

from __future__ import annotations

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QComboBox,
    QTabWidget, QListWidget, QListWidgetItem, QPushButton,
    QLineEdit, QAbstractItemView, QSizePolicy,
)
from PyQt6.QtCore import Qt, pyqtSignal

from igloo4.config import FAVOURITES, PLOT_MODES, FILE_MODES


class VariablePanel(QWidget):
    """Bottom-dock panel for variable selection and plot controls."""

    # Emitted when the user wants to add a variable to the plot
    add_variable_requested = pyqtSignal(str)
    # Emitted when the user wants to clear the plot
    clear_plot_requested = pyqtSignal()
    # Emitted when the user wants to export the plot
    export_png_requested = pyqtSignal()
    # Emitted when the plot mode changes
    plot_mode_changed = pyqtSignal(str)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._current_mode = list(FILE_MODES.keys())[0]
        self._build_ui()
        self._populate_favourites()

    # ------------------------------------------------------------------
    # UI construction
    # ------------------------------------------------------------------

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(6)

        # --- Variable tabs ---
        self._tabs = QTabWidget()

        # Favourites tab
        self._fav_list = QListWidget()
        self._fav_list.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self._fav_list.itemDoubleClicked.connect(
            lambda item: self.add_variable_requested.emit(item.text())
        )
        self._tabs.addTab(self._fav_list, "⭐  Favourites")

        # All-variables tab
        all_widget = QWidget()
        all_layout = QVBoxLayout(all_widget)
        all_layout.setContentsMargins(0, 0, 0, 0)
        self._search_box = QLineEdit()
        self._search_box.setPlaceholderText("Search variables…")
        self._search_box.textChanged.connect(self._filter_all_vars)
        all_layout.addWidget(self._search_box)
        self._all_list = QListWidget()
        self._all_list.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self._all_list.itemDoubleClicked.connect(
            lambda item: self.add_variable_requested.emit(item.text())
        )
        all_layout.addWidget(self._all_list)
        self._tabs.addTab(all_widget, "📋  All variables")

        layout.addWidget(self._tabs)

        # --- Controls row ---
        controls = QHBoxLayout()

        controls.addWidget(QLabel("Plot mode:"))
        self._plot_mode_combo = QComboBox()
        self._plot_mode_combo.addItems(PLOT_MODES)
        self._plot_mode_combo.currentTextChanged.connect(self.plot_mode_changed.emit)
        controls.addWidget(self._plot_mode_combo)

        controls.addStretch()

        self._add_btn = QPushButton("➕  Add to plot")
        self._add_btn.setToolTip("Double-click a variable or select one and click here")
        self._add_btn.clicked.connect(self._on_add_clicked)
        controls.addWidget(self._add_btn)

        self._clear_btn = QPushButton("🗑  Clear plot")
        self._clear_btn.clicked.connect(self.clear_plot_requested.emit)
        controls.addWidget(self._clear_btn)

        self._export_btn = QPushButton("💾  Export PNG")
        self._export_btn.clicked.connect(self.export_png_requested.emit)
        controls.addWidget(self._export_btn)

        layout.addLayout(controls)

    # ------------------------------------------------------------------
    # Public API (called from MainWindow)
    # ------------------------------------------------------------------

    def set_mode(self, mode: str) -> None:
        """Update favourites for the given file mode."""
        self._current_mode = mode
        self._populate_favourites()

    def populate_all_variables(self, varnames: list[str]) -> None:
        """Populate the 'All variables' tab with the given list."""
        self._all_vars: list[str] = varnames
        self._filter_all_vars(self._search_box.text())

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _populate_favourites(self) -> None:
        self._fav_list.clear()
        for name in FAVOURITES.get(self._current_mode, []):
            self._fav_list.addItem(name)

    def _filter_all_vars(self, text: str) -> None:
        self._all_list.clear()
        query = text.strip().lower()
        for name in getattr(self, "_all_vars", []):
            if not query or query in name.lower():
                self._all_list.addItem(name)

    def _on_add_clicked(self) -> None:
        """Add the currently selected variable (whichever tab is active)."""
        if self._tabs.currentIndex() == 0:
            items = self._fav_list.selectedItems()
        else:
            items = self._all_list.selectedItems()
        if items:
            self.add_variable_requested.emit(items[0].text())
