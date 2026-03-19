from __future__ import annotations

from textual import work
from textual.app import ComposeResult
from textual.binding import Binding
from textual.screen import Screen
from textual.widgets import DataTable, Footer, Header, Input, Static, Tree

from ipa_tui.widgets.detail import DetailPanel
from ipa_tui.widgets.sidebar import NavigationTree


def _val(v) -> str:
    if isinstance(v, list):
        return ", ".join(str(i) for i in v)
    if v is None:
        return ""
    return str(v)


DETAIL_SKIP_KEYS = {"dn", "objectclass", "ipauniqueid"}

LIST_COLUMNS = {
    "groups": {
        "columns": [("Group Name", "cn"), ("GID", "gidnumber"), ("Description", "description")],
        "name_key": "cn",
    },
    "users": {
        "columns": [("Login", "uid"), ("Full Name", "cn"), ("Email", "mail"), ("Status", "nsaccountlock")],
        "name_key": "uid",
    },
    "hbac_rules": {
        "columns": [("Rule Name", "cn"), ("Status", "ipaenabledflag"), ("Description", "description")],
        "name_key": "cn",
    },
    "sudo_rules": {
        "columns": [("Rule Name", "cn"), ("Status", "ipaenabledflag"), ("Description", "description")],
        "name_key": "cn",
    },
}


class MainScreen(Screen):
    BINDINGS = [
        Binding("q", "quit", "Quit"),
        Binding("escape", "go_back", "Back"),
        Binding("r", "refresh", "Refresh"),
        Binding("slash", "focus_filter", "Search", key_display="/"),
    ]

    CSS = """
    MainScreen {
        layout: horizontal;
    }

    #nav-tree {
        dock: left;
        width: 28;
        padding: 1;
        border-right: thick $accent;
        background: $surface;
    }

    DetailPanel {
        width: 1fr;
    }

    #filter-input {
        dock: top;
        margin: 0 1;
        display: none;
    }

    #filter-input.visible {
        display: block;
    }

    #section-title {
        dock: top;
        padding: 0 1;
        text-style: bold;
        color: $accent;
        background: $surface;
    }

    #detail-scroll {
        height: 1fr;
    }

    #data-table {
        height: auto;
    }

    #detail-text {
        padding: 1;
        display: none;
    }

    #detail-text.visible {
        display: block;
    }
    """

    def __init__(self) -> None:
        super().__init__()
        self._current_section: str | None = None
        self._current_data: list[dict] = []
        self._viewing_detail = False
        self._last_filter: str = ""

    def compose(self) -> ComposeResult:
        yield Header()
        yield NavigationTree()
        yield DetailPanel()
        yield Footer()

    def on_mount(self) -> None:
        table = self.query_one("#data-table", DataTable)
        table.cursor_type = "row"

    def on_tree_node_selected(self, event: Tree.NodeSelected) -> None:
        section = event.node.data
        if section:
            self._current_section = section
            self._viewing_detail = False
            self._load_section(section)

    def on_data_table_row_selected(self, event: DataTable.RowSelected) -> None:
        if self._viewing_detail or not self._current_section:
            return
        row_key = event.row_key
        meta = LIST_COLUMNS.get(self._current_section)
        if not meta:
            return
        name_key = meta["name_key"]
        for item in self._current_data:
            item_name = _val(item.get(name_key, ""))
            if item_name == str(row_key.value):
                self._load_detail(self._current_section, item_name)
                return

    def on_input_changed(self, event: Input.Changed) -> None:
        if event.input.id == "filter-input":
            self._last_filter = event.value
            if self._current_section != "users":
                self._apply_filter(event.value)

    def on_input_submitted(self, event: Input.Submitted) -> None:
        if event.input.id == "filter-input":
            if self._current_section == "users":
                self._search_users(event.value.strip())
            else:
                self.query_one("#data-table", DataTable).focus()

    def action_quit(self) -> None:
        self.app.exit()

    def action_go_back(self) -> None:
        filter_input = self.query_one("#filter-input", Input)
        if filter_input.has_class("visible") and filter_input.has_focus:
            filter_input.remove_class("visible")
            self.query_one("#data-table", DataTable).focus()
            return

        if self._viewing_detail and self._current_section:
            self._viewing_detail = False
            self._restore_list()
        else:
            self.query_one("#nav-tree", NavigationTree).focus()

    def action_refresh(self) -> None:
        if self._current_section:
            self._load_section(self._current_section)

    def action_focus_filter(self) -> None:
        if self._viewing_detail:
            return
        filter_input = self.query_one("#filter-input", Input)
        filter_input.add_class("visible")
        filter_input.focus()

    def _show_table(self) -> None:
        self.query_one("#data-table", DataTable).display = True
        detail_text = self.query_one("#detail-text", Static)
        detail_text.display = False
        detail_text.remove_class("visible")

    def _show_detail_text(self) -> None:
        self.query_one("#data-table", DataTable).display = False
        detail_text = self.query_one("#detail-text", Static)
        detail_text.display = True
        detail_text.add_class("visible")

    @work(thread=True)
    def _load_section(self, section: str) -> None:
        client = self.app.ipa_client
        title_map = {
            "my_info": "My Info",
            "groups": "Groups",
            "users": "Users",
            "hbac_rules": "HBAC Rules",
            "sudo_rules": "Sudo Rules",
        }
        self.app.call_from_thread(
            self.query_one("#section-title", Static).update,
            f" {title_map.get(section, section)} (loading...)",
        )

        try:
            if section == "my_info":
                data = client.get_my_info()
                self.app.call_from_thread(self._render_detail, "My Info", data)
                return

            if section == "users":
                self.app.call_from_thread(self._render_user_search)
                return

            loaders = {
                "groups": client.list_groups,
                "hbac_rules": client.list_hbac_rules,
                "sudo_rules": client.list_sudo_rules,
            }
            items = loaders[section]()
            self.app.call_from_thread(self._render_list, section, items)

        except Exception as e:
            self.app.call_from_thread(
                self.query_one("#section-title", Static).update,
                f"Error: {e}",
            )

    @work(thread=True)
    def _load_detail(self, section: str, name: str) -> None:
        client = self.app.ipa_client
        self.app.call_from_thread(
            self.query_one("#section-title", Static).update,
            f" {name} (loading...)",
        )

        try:
            show_methods = {
                "groups": ("show_group", name),
                "users": ("show_user", name),
                "hbac_rules": ("show_hbac_rule", name),
                "sudo_rules": ("show_sudo_rule", name),
            }
            method_name, arg = show_methods[section]
            data = getattr(client, method_name)(arg)
            self.app.call_from_thread(self._render_detail, name, data)
        except Exception as e:
            self.app.call_from_thread(
                self.query_one("#section-title", Static).update,
                f"Error: {e}",
            )

    def _render_list(self, section: str, items: list[dict]) -> None:
        self._current_data = items
        self._last_filter = ""
        self._show_table()
        self.query_one("#filter-input", Input).value = ""

        title_map = {
            "groups": "Groups",
            "users": "Users",
            "hbac_rules": "HBAC Rules",
            "sudo_rules": "Sudo Rules",
        }
        self.query_one("#section-title", Static).update(
            f" {title_map.get(section, section)} ({len(items)} items)"
        )

        table = self.query_one("#data-table", DataTable)
        table.clear(columns=True)

        meta = LIST_COLUMNS.get(section)
        if not meta:
            return

        for col_label, _ in meta["columns"]:
            table.add_column(col_label, key=col_label)

        for item in items:
            name_val = _val(item.get(meta["name_key"], ""))
            row = []
            for _, field in meta["columns"]:
                row.append(_val(item.get(field, "")))
            table.add_row(*row, key=name_val)

        table.focus()

    def _render_detail(self, title: str, data: dict) -> None:
        self._viewing_detail = True
        self._show_detail_text()
        self.query_one("#section-title", Static).update(f" {title}")

        lines = []
        for key, value in sorted(data.items()):
            if key.lower() in DETAIL_SKIP_KEYS:
                continue
            lines.append(f"[bold]{key}[/bold]: {_val(value)}")

        text = "\n".join(lines) if lines else "No data"
        detail = self.query_one("#detail-text", Static)
        detail.update(text)

    def _render_user_search(self) -> None:
        self._current_data = []
        self._last_filter = ""
        self._show_table()
        table = self.query_one("#data-table", DataTable)
        table.clear(columns=True)
        meta = LIST_COLUMNS["users"]
        for col_label, _ in meta["columns"]:
            table.add_column(col_label, key=col_label)
        self.query_one("#section-title", Static).update(
            " Users — type query and press Enter"
        )
        filter_input = self.query_one("#filter-input", Input)
        filter_input.value = ""
        filter_input.placeholder = "Search users (Enter to query)..."
        filter_input.add_class("visible")
        filter_input.focus()

    @work(thread=True)
    def _search_users(self, query: str) -> None:
        if not query:
            return
        client = self.app.ipa_client
        self.app.call_from_thread(
            self.query_one("#section-title", Static).update,
            f" Users — searching '{query}'...",
        )
        try:
            items = client.search_users(query)
            self.app.call_from_thread(self._render_user_results, query, items)
        except Exception as e:
            self.app.call_from_thread(
                self.query_one("#section-title", Static).update,
                f"Error: {e}",
            )

    def _render_user_results(self, query: str, items: list[dict]) -> None:
        self._current_data = items
        self._show_table()
        table = self.query_one("#data-table", DataTable)
        table.clear(columns=True)
        meta = LIST_COLUMNS["users"]
        for col_label, _ in meta["columns"]:
            table.add_column(col_label, key=col_label)
        for item in items:
            name_val = _val(item.get(meta["name_key"], ""))
            row = [_val(item.get(field, "")) for _, field in meta["columns"]]
            table.add_row(*row, key=name_val)
        self.query_one("#section-title", Static).update(
            f" Users — '{query}' ({len(items)} results)"
        )
        table.focus()

    def _restore_list(self) -> None:
        if self._current_section == "users":
            self._render_user_results(self._last_filter, self._current_data)
            filter_input = self.query_one("#filter-input", Input)
            filter_input.value = self._last_filter
            filter_input.add_class("visible")
            return
        self._show_table()
        filter_input = self.query_one("#filter-input", Input)
        if self._last_filter:
            filter_input.value = self._last_filter
            filter_input.add_class("visible")
            self._apply_filter(self._last_filter)
        else:
            self._apply_filter("")
        self.query_one("#data-table", DataTable).focus()

    def _apply_filter(self, query: str) -> None:
        if self._viewing_detail or not self._current_section:
            return

        meta = LIST_COLUMNS.get(self._current_section)
        if not meta:
            return

        table = self.query_one("#data-table", DataTable)
        table.clear(columns=True)

        for col_label, _ in meta["columns"]:
            table.add_column(col_label, key=col_label)

        q = query.lower()
        count = 0
        for item in self._current_data:
            row_values = []
            for _, field in meta["columns"]:
                row_values.append(_val(item.get(field, "")))
            if q and not any(q in v.lower() for v in row_values):
                continue
            name_val = _val(item.get(meta["name_key"], ""))
            table.add_row(*row_values, key=name_val)
            count += 1

        title_map = {
            "groups": "Groups",
            "users": "Users",
            "hbac_rules": "HBAC Rules",
            "sudo_rules": "Sudo Rules",
        }
        section_title = title_map.get(self._current_section, self._current_section)
        suffix = f" (filtered: {count}/{len(self._current_data)})" if q else f" ({count} items)"
        self.query_one("#section-title", Static).update(f" {section_title}{suffix}")
