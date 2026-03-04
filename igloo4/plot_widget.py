"""
plot_widget.py — Central matplotlib canvas with an embedded Qt toolbar.

Supports:
  • vs Time   — variables on left / additional right Y-axes (twinx)
  • vs Depth  — inverted depth Y-axis, variables on X-axes
  • vs Each Other — two-variable scatter plot
"""

from __future__ import annotations

import datetime
from typing import TYPE_CHECKING

import numpy as np
import matplotlib
matplotlib.use("QtAgg")
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qtagg import (
    FigureCanvasQTAgg as FigureCanvas,
    NavigationToolbar2QT as NavigationToolbar,
)
from matplotlib.figure import Figure
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QFileDialog, QMessageBox
from PyQt6.QtCore import Qt

if TYPE_CHECKING:
    from igloo4.data_manager import DataManager

# Colour cycle for successive variables
_COLOURS = plt.rcParams["axes.prop_cycle"].by_key()["color"]


class PlotWidget(QWidget):
    """Container holding the matplotlib figure and its navigation toolbar."""

    def __init__(self, data_manager: "DataManager", parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._dm = data_manager
        self._plot_mode = "vs Time"   # current plot mode

        # Track what is plotted: list of (varname, ax, line_handle)
        self._plotted: list[tuple[str, object, object]] = []
        # Map unit → axis (for shared-unit axes)
        self._unit_axes: dict[str, object] = {}

        self._fig = Figure(figsize=(8, 5), tight_layout=True)
        self._canvas = FigureCanvas(self._fig)
        self._toolbar = NavigationToolbar(self._canvas, self)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self._toolbar)
        layout.addWidget(self._canvas)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def set_plot_mode(self, mode: str) -> None:
        self._plot_mode = mode

    def add_variable(self, varname: str) -> None:
        """Add *varname* to the current plot."""
        if not self._dm.is_loaded():
            QMessageBox.warning(self, "No data", "Please load files first.")
            return

        # Prevent duplicates
        if any(v == varname for v, _, _ in self._plotted):
            QMessageBox.information(self, "Already plotted",
                                    f"'{varname}' is already on the plot.")
            return

        # "vs Each Other" only allows exactly two variables
        if self._plot_mode == "vs Each Other" and len(self._plotted) >= 2:
            QMessageBox.warning(self, "Too many variables",
                                "'vs Each Other' supports at most two variables.\n"
                                "Clear the plot first.")
            return

        try:
            t, v = self._dm.get(varname)
        except ValueError as exc:
            QMessageBox.warning(self, "Data error", str(exc))
            return

        if len(t) == 0:
            QMessageBox.information(self, "No data", f"'{varname}' has no data in the loaded files.")
            return

        colour = _COLOURS[len(self._plotted) % len(_COLOURS)]
        unit = self._dm.unit(varname)

        if self._plot_mode == "vs Time":
            self._add_vs_time(varname, t, v, unit, colour)
        elif self._plot_mode == "vs Depth":
            self._add_vs_depth(varname, t, v, unit, colour)
        else:  # vs Each Other
            self._add_vs_each_other(varname, t, v, unit, colour)

        self._canvas.draw()

    def clear_plot(self) -> None:
        """Remove all traces and reset the figure."""
        self._fig.clear()
        self._plotted.clear()
        self._unit_axes.clear()
        self._canvas.draw()

    def export_png(self) -> None:
        """Open a save-file dialog and export the figure to PNG."""
        path, _ = QFileDialog.getSaveFileName(
            self, "Export plot as PNG", "", "PNG files (*.png)"
        )
        if path:
            if not path.lower().endswith(".png"):
                path += ".png"
            from igloo4.config import EXPORT_DPI
            self._fig.savefig(path, dpi=EXPORT_DPI, bbox_inches="tight")
            QMessageBox.information(self, "Exported", f"Plot saved to:\n{path}")

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _primary_ax(self) -> object:
        """Return (or create) the primary (leftmost) axis."""
        if not self._fig.axes:
            ax = self._fig.add_subplot(111)
        else:
            ax = self._fig.axes[0]
        return ax

    def _add_vs_time(self, varname: str, t: np.ndarray, v: np.ndarray,
                     unit: str, colour: str) -> None:
        """Plot variable on the time axis, adding a new twinx for different units."""
        import matplotlib.dates as mdates

        # Convert Unix timestamps → datetime objects for nice axis labels
        times = [datetime.datetime.fromtimestamp(ts) for ts in t]

        primary = self._primary_ax()

        if not self._plotted:
            # First variable → use primary axis
            ax = primary
            ax.set_xlabel("Time")
            ax.tick_params(axis="x", rotation=30)
            ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m-%d\n%H:%M"))
        elif unit in self._unit_axes:
            ax = self._unit_axes[unit]
        else:
            # New unit → twin the primary axis
            ax = primary.twinx()
            # Offset additional right spines so they don't overlap
            n_extra = len(self._fig.axes) - 1
            if n_extra > 1:
                ax.spines["right"].set_position(("outward", 60 * (n_extra - 1)))

        line, = ax.plot(times, v, color=colour,
                        label=f"{varname} [{unit}]" if unit else varname)
        ax.set_ylabel(_axis_label(unit), color=colour)
        ax.tick_params(axis="y", colors=colour)

        self._unit_axes.setdefault(unit, ax)
        self._plotted.append((varname, ax, line))
        _update_legend(self._fig)

    def _add_vs_depth(self, varname: str, t: np.ndarray, v: np.ndarray,
                      unit: str, colour: str) -> None:
        """Plot variable on an X-axis against depth on the Y-axis."""
        from igloo4.config import DEPTH_VARIABLE

        try:
            t_dep, depth = self._dm.get(DEPTH_VARIABLE)
        except ValueError:
            QMessageBox.warning(self, "No depth data",
                                f"Could not retrieve '{DEPTH_VARIABLE}' for depth axis.")
            return

        # Interpolate depth onto the variable's timestamps
        depth_interp = np.interp(t, t_dep, depth, left=np.nan, right=np.nan)

        primary = self._primary_ax()

        if not self._plotted:
            ax = primary
            ax.set_ylabel("Depth (m)")
            ax.invert_yaxis()
        elif unit in self._unit_axes:
            ax = self._unit_axes[unit]
        else:
            ax = primary.twiny()
            n_extra = len(self._fig.axes) - 1
            if n_extra > 1:
                ax.spines["top"].set_position(("outward", 40 * (n_extra - 1)))

        line, = ax.plot(v, depth_interp, color=colour,
                        label=f"{varname} [{unit}]" if unit else varname)
        ax.set_xlabel(_axis_label(unit), color=colour)
        ax.tick_params(axis="x", colors=colour)

        self._unit_axes.setdefault(unit, ax)
        self._plotted.append((varname, ax, line))
        _update_legend(self._fig)

    def _add_vs_each_other(self, varname: str, t: np.ndarray, v: np.ndarray,
                            unit: str, colour: str) -> None:
        """Scatter plot of two variables against each other."""
        ax = self._primary_ax()

        if not self._plotted:
            # First variable stored; nothing drawn yet
            self._unit_axes["_x"] = (varname, t, v, unit)
            self._plotted.append((varname, ax, None))
            ax.set_xlabel(_axis_label(unit) or varname)
        else:
            x_varname, t_x, x_vals, x_unit = self._unit_axes["_x"]
            # Interpolate x onto y's timestamps for alignment
            x_interp = np.interp(t, t_x, x_vals, left=np.nan, right=np.nan)
            mask = ~(np.isnan(x_interp) | np.isnan(v))
            line, = ax.plot(x_interp[mask], v[mask], ".", color=colour, markersize=3,
                            label=f"{x_varname} vs {varname}")
            ax.set_xlabel(_axis_label(x_unit) or x_varname)
            ax.set_ylabel(_axis_label(unit) or varname)
            ax.set_title(f"{x_varname}  vs  {varname}")
            self._plotted.append((varname, ax, line))
            _update_legend(self._fig)


# ------------------------------------------------------------------
# Module-level helpers
# ------------------------------------------------------------------

def _axis_label(unit: str) -> str:
    return f"[{unit}]" if unit else ""


def _update_legend(fig: Figure) -> None:
    """Collect handles/labels from all axes and put a single legend on the first axis."""
    all_handles, all_labels = [], []
    for ax in fig.axes:
        h, l = ax.get_legend_handles_labels()
        all_handles.extend(h)
        all_labels.extend(l)
    if all_handles:
        fig.axes[0].legend(all_handles, all_labels, loc="best", fontsize=8)
