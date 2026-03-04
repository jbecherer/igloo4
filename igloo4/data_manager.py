"""
data_manager.py — dbdreader wrapper.

Handles loading one or more dbd/ebd or sbd/tbd files via MultiDBD,
caching results, and providing a clean API to the rest of the app.
"""

from __future__ import annotations

import numpy as np
import dbdreader


class DataManager:
    """Thin wrapper around dbdreader.MultiDBD with caching."""

    def __init__(self) -> None:
        self._mdb: dbdreader.MultiDBD | None = None
        self._cache: dict[str, tuple[np.ndarray, np.ndarray]] = {}
        self._units: dict[str, str] = {}
        self._parameter_names: list[str] = []

    # ------------------------------------------------------------------
    # Loading
    # ------------------------------------------------------------------

    def load(self, filenames: list[str]) -> None:
        """Load a list of glider files (any mix of dbd/ebd/sbd/tbd)."""
        self._mdb = dbdreader.MultiDBD(filenames=filenames)
        self._cache.clear()
        self._units = dict(self._mdb.parameterUnits)

        # Flatten eng + sci parameter name lists into a single sorted list
        pnames: set[str] = set()
        raw = self._mdb.parameterNames
        for category in ("eng", "sci"):
            pnames.update(raw.get(category, []))
        self._parameter_names = sorted(pnames)

    def is_loaded(self) -> bool:
        return self._mdb is not None

    def clear(self) -> None:
        self._mdb = None
        self._cache.clear()
        self._units.clear()
        self._parameter_names.clear()

    # ------------------------------------------------------------------
    # Queries
    # ------------------------------------------------------------------

    @property
    def parameter_names(self) -> list[str]:
        return self._parameter_names

    def unit(self, varname: str) -> str:
        return self._units.get(varname, "")

    def get(self, varname: str) -> tuple[np.ndarray, np.ndarray]:
        """Return (time_array, value_array) for *varname*.

        Time values are Unix epoch floats (seconds since 1970-01-01).
        Results are cached after the first call.
        """
        if varname in self._cache:
            return self._cache[varname]

        if self._mdb is None:
            raise RuntimeError("No files loaded.")

        try:
            t, v = self._mdb.get(varname)
        except Exception as exc:
            raise ValueError(f"Cannot retrieve '{varname}': {exc}") from exc

        t = np.asarray(t, dtype=float)
        v = np.asarray(v, dtype=float)
        self._cache[varname] = (t, v)
        return t, v

    def has_variable(self, varname: str) -> bool:
        return varname in self._parameter_names
