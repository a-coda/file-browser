"""
File browser example.

Run with:

    python file_browser.py PATH
"""

from __future__ import annotations

import sys
from pathlib import Path
import os
import datetime

from rich.syntax import Syntax
from rich.traceback import Traceback

from textual.app import App, ComposeResult
from textual.containers import Container, VerticalScroll
from textual.reactive import reactive, var
from textual.widgets import DirectoryTree, Footer, Header, DataTable, Log


class FileBrowser(App):
    """File and folder browser app."""

    CSS_PATH = "file_browser.tcss"
    BINDINGS = [
        ("f", "toggle_tree", "Toggle Tree"),
        ("q", "quit", "Quit"),
    ]

    column_names = ["Name", "Size", "Modified"]
    sort_column = "Name"
    sort_reverse = False
    show_tree = var(True)
    data_by_key = []
    selected_row = None
    path: reactive[str | None] = reactive(None)

    def watch_show_tree(self, show_tree: bool) -> None:
        """Called when show_tree is modified."""
        self.set_class(show_tree, "-show-tree")

    def compose(self) -> ComposeResult:
        """Compose our UI."""
        path = Path.home()
        yield Header()
        with Container():
            yield DirectoryOnlyTree(path, id="tree-view")
            with VerticalScroll(id="data-view"):
                yield DataTable(id="data", cursor_type="row")
            with VerticalScroll(id="log-view"):
                yield Log()
        yield Footer()

    def on_mount(self) -> None:
        self.query_one(DirectoryOnlyTree).focus()
        self.query_one(DataTable).add_columns(*self.column_names)
        def theme_change(_signal) -> None:
            """Force the syntax to use a different theme."""
            self.watch_path(self.path)

        self.theme_changed_signal.subscribe(self, theme_change)

    def on_data_table_row_selected(self, event):
        self.selected_row = event.row_key

    def _on_click(self, event):
        if event.widget == self.query_one(DataTable) and self.selected_row is not None and event.chain == 2:
            os.startfile(self.data_by_row[self.selected_row].path)

    def on_directory_tree_directory_selected(
        self, event: DirectoryTree.FileSelected
    ) -> None:
        """Called when the user click a directory in the directory tree."""
        event.stop()
        self.path = str(event.path)

    def on_data_table_header_selected(self, event: DataTable.HeaderSelected):
        if self.sort_column == event.column_key:
            self.sort_reverse = not self.sort_reverse
        else:
            self.sort_reverse = False
            self.sort_column = event.column_key
        event.data_table.sort(self.sort_column,
                              key = parse_human_readable_byte_count_si if event.column_index == self.column_names.index("Size") else lambda x: x,
                              reverse = self.sort_reverse)

    def watch_path(self, path: str | None) -> None:
        """Called when path changes."""
        data_view = self.query_one("#data", DataTable)
        if path is None:
            return

        try:
            data_view.clear()
            self.data_by_key = {}
            data_values = list(os.scandir(path))
            data_keys = data_view.add_rows([[item.name, human_readable_byte_count_si(item.stat().st_size), datetime.datetime.fromtimestamp(item.stat().st_mtime)] for item in data_values])
            for key, value in zip(data_keys, data_values):
                self.data_by_key[key] = value
            
        except Exception as e:
            log = self.query_one(Log)
            log.write_line(str(e))

    def action_toggle_tree(self) -> None:
        """Called in response to key binding."""
        self.show_tree = not self.show_tree


class DirectoryOnlyTree(DirectoryTree):
    def filter_paths(self, paths):
        return [path for path in paths if os.path.isdir(path)]


def human_readable_byte_count_si(n):
    if -1000 < n and n < 1000:
        return str(n) + " B"

    prefixes = "kMGTPE"
    p = 0
    while n <= -999950 or n >= 999950:
        n /= 1000
        p += 1
    
    return "%.1f %sB" % (n / 1000.0, prefixes[p])

def parse_human_readable_byte_count_si(n):
    prefixes = "BkMGTPE"
    number, units = n.split()
    return float(number) * pow(1000, prefixes.index(units[0]))

if __name__ == "__main__":
    FileBrowser().run()
