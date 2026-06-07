# ui/widgets.py
"""Custom ttk/ttkbootstrap widgets for Codex Transfer."""
from __future__ import annotations

import tkinter as tk
from tkinter import ttk
from typing import Any


class CheckboxTreeview(ttk.Treeview):
    """Treeview with a checkbox column for multi-selection."""

    def __init__(self, master: Any, **kwargs: Any) -> None:
        super().__init__(master, **kwargs)
        self._checked: set[str] = set()
        self._checkbox_column: str = "#0"
        self.bind("<Button-1>", self._on_click, add=True)

    def _on_click(self, event: tk.Event) -> None:
        region = self.identify_region(event.x, event.y)
        if region != "tree" and region != "cell":
            return
        item = self.identify_row(event.y)
        if not item:
            return
        self.toggle_checked(item)

    def toggle_checked(self, item: str) -> None:
        if item in self._checked:
            self._checked.discard(item)
            self._update_item_display(item, checked=False)
        else:
            self._checked.add(item)
            self._update_item_display(item, checked=True)

    def _update_item_display(self, item: str, checked: bool) -> None:
        values = list(self.item(item, "values"))
        if values:
            values[0] = "☑" if checked else "☐"
            self.item(item, values=values)

    def set_checked(self, item: str, checked: bool) -> None:
        if checked:
            self._checked.add(item)
        else:
            self._checked.discard(item)
        self._update_item_display(item, checked)

    def check_all(self) -> None:
        for item in self.get_children():
            self._checked.add(item)
            self._update_item_display(item, checked=True)

    def uncheck_all(self) -> None:
        for item in self.get_children():
            self._checked.discard(item)
            self._update_item_display(item, checked=False)

    def invert_checked(self) -> None:
        for item in self.get_children():
            if item in self._checked:
                self._checked.discard(item)
                self._update_item_display(item, checked=False)
            else:
                self._checked.add(item)
                self._update_item_display(item, checked=True)

    def get_checked_ids(self) -> list[str]:
        return [item for item in self._checked if item in self.get_children()]

    def clear_checked(self) -> None:
        for item in list(self._checked):
            if item in self.get_children():
                self._update_item_display(item, checked=False)
        self._checked.clear()

    def insert(self, parent: str, index: str | int = tk.END, **kwargs: Any) -> str:
        values = kwargs.get("values", ())
        if isinstance(values, (list, tuple)):
            values = ("☐",) + tuple(values)
        kwargs["values"] = values
        return super().insert(parent, index, **kwargs)
