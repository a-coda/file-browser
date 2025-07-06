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
from textual.widgets import DirectoryTree, Footer, Header, DataTable


class FileBrowser(App):
    """File and folder browser app."""

    CSS_PATH = "file_browser.tcss"
    BINDINGS = [
        ("f", "toggle_tree", "Toggle Tree"),
        ("q", "quit", "Quit"),
    ]

    show_tree = var(True)
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
                yield DataTable(id="data")
        yield Footer()

    def on_mount(self) -> None:
        self.query_one(DirectoryOnlyTree).focus()
        self.query_one(DataTable).add_columns("Name", "Size", "Modified")
        def theme_change(_signal) -> None:
            """Force the syntax to use a different theme."""
            self.watch_path(self.path)

        self.theme_changed_signal.subscribe(self, theme_change)

    def on_directory_tree_directory_selected(
        self, event: DirectoryTree.FileSelected
    ) -> None:
        """Called when the user click a directory in the directory tree."""
        event.stop()
        self.path = str(event.path)

    def watch_path(self, path: str | None) -> None:
        """Called when path changes."""
        data_view = self.query_one("#data", DataTable)
        if path is None:
            return

        try:
            data_view.clear()
            data_view.add_rows([[item.name, human_readable_byte_count_si(item.stat().st_size), datetime.datetime.fromtimestamp(item.stat().st_mtime)] for item in os.scandir(path)])
        except Exception as e:
            data_view.add_rows([[e, 0, 0]])

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


if __name__ == "__main__":
    FileBrowser().run()
