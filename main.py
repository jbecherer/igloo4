"""
main.py — Entry point for the Igloo4 Slocum Glider Viewer.

Run with:
    uv run python main.py
"""

import sys
import matplotlib
matplotlib.use("QtAgg")

from PyQt6.QtWidgets import QApplication
from igloo4.main_window import MainWindow


def main() -> None:
    app = QApplication(sys.argv)
    app.setApplicationName("Igloo4")
    app.setOrganizationName("Hereon GliderLab")

    window = MainWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
