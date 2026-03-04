"""
main_window.py — Top-level QMainWindow.

Assembles the three main panels as docked widgets and wires up all signals.
"""

from __future__ import annotations

from PyQt6.QtWidgets import (
    QMainWindow, QDockWidget, QStatusBar, QMessageBox,
    QMenuBar, QMenu,
)
from PyQt6.QtCore import Qt

from igloo4.data_manager import DataManager
from igloo4.file_browser import FileBrowser
from igloo4.variable_panel import VariablePanel
from igloo4.plot_widget import PlotWidget


class MainWindow(QMainWindow):
    """Main application window."""

    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Igloo4 — Slocum Glider Viewer")
        self.resize(1280, 800)

        self._dm = DataManager()

        # --- Central widget: plot ---
        self._plot = PlotWidget(self._dm)
        self.setCentralWidget(self._plot)

        # --- Left dock: file browser ---
        self._browser = FileBrowser()
        left_dock = QDockWidget("Files", self)
        left_dock.setObjectName("files_dock")
        left_dock.setWidget(self._browser)
        left_dock.setAllowedAreas(Qt.DockWidgetArea.LeftDockWidgetArea |
                                   Qt.DockWidgetArea.RightDockWidgetArea)
        self.addDockWidget(Qt.DockWidgetArea.LeftDockWidgetArea, left_dock)
        left_dock.setMinimumWidth(280)

        # --- Bottom dock: variable panel ---
        self._var_panel = VariablePanel()
        bottom_dock = QDockWidget("Variables & Plot Controls", self)
        bottom_dock.setObjectName("variables_dock")
        bottom_dock.setWidget(self._var_panel)
        bottom_dock.setAllowedAreas(Qt.DockWidgetArea.BottomDockWidgetArea |
                                     Qt.DockWidgetArea.TopDockWidgetArea)
        self.addDockWidget(Qt.DockWidgetArea.BottomDockWidgetArea, bottom_dock)
        bottom_dock.setMinimumHeight(180)

        # --- Status bar ---
        self._status = QStatusBar()
        self.setStatusBar(self._status)
        self._status.showMessage("Ready — select a file mode and load files to begin.")

        # --- Menu bar ---
        self._build_menu(left_dock, bottom_dock)

        # --- Connect signals ---
        self._browser.files_load_requested.connect(self._on_load_files)
        self._browser._mode_combo.currentTextChanged.connect(self._on_mode_changed)

        self._var_panel.add_variable_requested.connect(self._plot.add_variable)
        self._var_panel.clear_plot_requested.connect(self._plot.clear_plot)
        self._var_panel.export_png_requested.connect(self._plot.export_png)
        self._var_panel.plot_mode_changed.connect(self._plot.set_plot_mode)

    # ------------------------------------------------------------------
    # Menu
    # ------------------------------------------------------------------

    def _build_menu(self, left_dock: QDockWidget, bottom_dock: QDockWidget) -> None:
        menu_bar = self.menuBar()

        # File menu
        file_menu: QMenu = menu_bar.addMenu("&File")
        file_menu.addAction("&Export plot as PNG…", self._plot.export_png)
        file_menu.addSeparator()
        file_menu.addAction("&Quit", self.close)

        # View menu — toggle docks
        view_menu: QMenu = menu_bar.addMenu("&View")
        view_menu.addAction(left_dock.toggleViewAction())
        view_menu.addAction(bottom_dock.toggleViewAction())

        # Help menu
        help_menu: QMenu = menu_bar.addMenu("&Help")
        help_menu.addAction("&About", self._show_about)

    # ------------------------------------------------------------------
    # Slots
    # ------------------------------------------------------------------

    def _on_load_files(self, paths: list[str]) -> None:
        self._status.showMessage(f"Loading {len(paths)} file(s)…")
        try:
            self._dm.load(paths)
        except Exception as exc:
            QMessageBox.critical(self, "Load error", str(exc))
            self._status.showMessage("Error loading files.")
            return

        # Clear existing plot since data changed
        self._plot.clear_plot()

        # Populate all-variables tab
        self._var_panel.populate_all_variables(self._dm.parameter_names)

        n = len(self._dm.parameter_names)
        self._status.showMessage(
            f"Loaded {len(paths)} file(s) — {n} variables available."
        )

    def _on_mode_changed(self, mode: str) -> None:
        self._var_panel.set_mode(mode)
        self._dm.clear()
        self._plot.clear_plot()
        self._var_panel.populate_all_variables([])
        self._status.showMessage("Mode changed — please load files.")

    def _show_about(self) -> None:
        QMessageBox.about(
            self,
            "About Igloo4",
            "<b>Igloo4</b> — Slocum Glider Data Viewer<br><br>"
            "Reads dbd/ebd/sbd/tbd files via <tt>dbdreader</tt>.<br>"
            "Built with PyQt6 and matplotlib.",
        )
