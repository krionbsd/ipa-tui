from __future__ import annotations

from textual.app import ComposeResult
from textual.containers import Vertical, VerticalScroll
from textual.widgets import DataTable, Input, Static


class DetailPanel(Vertical):
    def compose(self) -> ComposeResult:
        yield Input(placeholder="Search / filter...", id="filter-input")
        yield Static("", id="section-title")
        with VerticalScroll(id="detail-scroll"):
            yield DataTable(id="data-table")
            yield Static("", id="detail-text")
