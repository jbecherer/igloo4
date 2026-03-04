"""
file_browser.py — Left dock panel.

Contains:
  • Mode selector (dbd+ebd / sbd+tbd)
  • Folder-tree browser filtered to the relevant extensions
  • List of currently selected files
  • "Load selected files" button
"""

from __future__ import annotations

import os
from typing import Callable

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QComboBox,
    QTreeView, QListWidget, QListWidgetItem, QPushButton,
    QAbstractItemView, QSizePolicy,
    QToolButton, QFileDialog,
)
from PyQt6.QtCore import Qt, QDir, QSortFilterProxyModel, QModelIndex, pyqtSignal
from PyQt6.QtGui import QIcon, QFileSystemModel

from igloo4.config import FILE_MODES


class _ExtensionFilterProxy(QSortFilterProxyModel):
    """Show only directories and files whose extension matches the current set."""

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._extensions: set[str] = set()

    def set_extensions(self, exts: set[str]) -> None:
        self._extensions = {e.lower() for e in exts}
        self.invalidateFilter()

    def filterAcceptsRow(self, source_row: int, source_parent: QModelIndex) -> bool:
        model: QFileSystemModel = self.sourceModel()  # type: ignore[assignment]
        idx = model.index(source_row, 0, source_parent)
        info = model.fileInfo(idx)
        if info.isDir():
            return True
        return info.suffix().lower() in self._extensions


class FileBrowser(QWidget):
    """Left-dock widget for mode selection and file browsing."""

    # Emitted when the user clicks "Load files"; payload = list of file paths
    files_load_requested = pyqtSignal(list)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._build_ui()
        self._refresh_mode()

    # ------------------------------------------------------------------
    # UI construction
    # ------------------------------------------------------------------

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(6)

        # --- Mode selector ---
        layout.addWidget(QLabel("<b>File mode</b>"))
        self._mode_combo = QComboBox()
        self._mode_combo.addItems(list(FILE_MODES.keys()))
        self._mode_combo.currentTextChanged.connect(self._refresh_mode)
        layout.addWidget(self._mode_combo)

        # --- Root folder picker ---
        folder_row = QHBoxLayout()
        self._root_label = QLabel("Folder:")
        folder_row.addWidget(self._root_label)
        self._folder_btn = QToolButton()
        self._folder_btn.setText("…")
        self._folder_btn.setToolTip("Choose root folder")
        self._folder_btn.clicked.connect(self._pick_folder)
        folder_row.addWidget(self._folder_btn)
        layout.addLayout(folder_row)

        # --- Folder tree ---
        layout.addWidget(QLabel("<b>Browse</b>"))
        self._fs_model = QFileSystemModel()
        self._fs_model.setRootPath(QDir.homePath())

        self._proxy = _ExtensionFilterProxy()
        self._proxy.setSourceModel(self._fs_model)

        self._tree = QTreeView()
        self._tree.setModel(self._proxy)
        self._tree.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        # Hide unnecessary columns (size, type, date)
        for col in (1, 2, 3):
            self._tree.hideColumn(col)
        self._tree.setSortingEnabled(True)
        self._tree.setAnimated(True)
        self._tree.setMinimumHeight(200)
        self._tree.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

        # Start at home directory
        home_src = self._fs_model.index(QDir.homePath())
        home_proxy = self._proxy.mapFromSource(home_src)
        self._tree.setRootIndex(home_proxy)
        self._tree.expand(home_proxy)

        layout.addWidget(self._tree)

        # --- Add selected files button ---
        self._add_btn = QPushButton("➕  Add selected to list")
        self._add_btn.clicked.connect(self._add_selected)
        layout.addWidget(self._add_btn)

        # --- Selected files list ---
        layout.addWidget(QLabel("<b>Selected files</b>"))
        self._file_list = QListWidget()
        self._file_list.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        self._file_list.setMinimumHeight(80)
        self._file_list.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        layout.addWidget(self._file_list)

        # --- Remove / Clear buttons ---
        btn_row = QHBoxLayout()
        self._remove_btn = QPushButton("Remove")
        self._remove_btn.clicked.connect(self._remove_selected)
        self._clear_btn = QPushButton("Clear list")
        self._clear_btn.clicked.connect(self._file_list.clear)
        btn_row.addWidget(self._remove_btn)
        btn_row.addWidget(self._clear_btn)
        layout.addLayout(btn_row)

        # --- Load button ---
        self._load_btn = QPushButton("⬆  Load files")
        self._load_btn.setStyleSheet("font-weight: bold; padding: 6px;")
        self._load_btn.clicked.connect(self._emit_load)
        layout.addWidget(self._load_btn)

    # ------------------------------------------------------------------
    # Mode / folder helpers
    # ------------------------------------------------------------------

    def _refresh_mode(self) -> None:
        mode = self._mode_combo.currentText()
        exts = set(FILE_MODES[mode])
        self._proxy.set_extensions(exts)
        # Reset file list when mode changes
        self._file_list.clear()

    def _pick_folder(self) -> None:
        folder = QFileDialog.getExistingDirectory(
            self, "Choose root folder", QDir.homePath()
        )
        if folder:
            src_idx = self._fs_model.setRootPath(folder)
            proxy_idx = self._proxy.mapFromSource(src_idx)
            self._tree.setRootIndex(proxy_idx)
            self._tree.expand(proxy_idx)

    # ------------------------------------------------------------------
    # File selection helpers
    # ------------------------------------------------------------------

    def _add_selected(self) -> None:
        """Add files selected in the tree view to the selected-files list."""
        mode = self._mode_combo.currentText()
        exts = {e.lower() for e in FILE_MODES[mode]}

        existing = {self._file_list.item(i).text()
                    for i in range(self._file_list.count())}

        for proxy_idx in self._tree.selectedIndexes():
            if proxy_idx.column() != 0:
                continue
            src_idx = self._proxy.mapToSource(proxy_idx)
            info = self._fs_model.fileInfo(src_idx)
            if info.isDir():
                # Add all matching files in the directory
                for entry in os.scandir(info.absoluteFilePath()):
                    if entry.is_file() and entry.name.rsplit(".", 1)[-1].lower() in exts:
                        if entry.path not in existing:
                            self._file_list.addItem(entry.path)
                            existing.add(entry.path)
            elif info.suffix().lower() in exts:
                path = info.absoluteFilePath()
                if path not in existing:
                    self._file_list.addItem(path)
                    existing.add(path)

    def _remove_selected(self) -> None:
        for item in self._file_list.selectedItems():
            self._file_list.takeItem(self._file_list.row(item))

    def _emit_load(self) -> None:
        paths = [self._file_list.item(i).text()
                 for i in range(self._file_list.count())]
        if paths:
            self.files_load_requested.emit(paths)

    # ------------------------------------------------------------------
    # Public helpers
    # ------------------------------------------------------------------

    @property
    def current_mode(self) -> str:
        return self._mode_combo.currentText()
