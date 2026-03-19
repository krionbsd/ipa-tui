from __future__ import annotations

from textual import work
from textual.app import ComposeResult
from textual.containers import Center, Vertical
from textual.screen import Screen
from textual.widgets import Button, Input, Label, Static

from ipa_tui.client import IPAClient
from ipa_tui.config import IPAConfig

_DEFAULTS = IPAConfig()


class LoginScreen(Screen):
    CSS = """
    LoginScreen {
        align: center middle;
    }

    #login-box {
        width: 60;
        height: auto;
        padding: 1 2;
        border: thick $accent;
        background: $surface;
    }

    #login-title {
        text-align: center;
        text-style: bold;
        margin-bottom: 1;
        width: 100%;
    }

    #login-box Label {
        margin-top: 1;
    }

    #login-box Input {
        margin-bottom: 0;
    }

    #login-btn {
        margin-top: 1;
        width: 100%;
    }

    #login-error {
        color: $error;
        text-align: center;
        margin-top: 1;
        width: 100%;
    }
    """

    def compose(self) -> ComposeResult:
        with Center():
            with Vertical(id="login-box"):
                yield Static("FreeIPA TUI", id="login-title")
                yield Label("Host")
                yield Input(
                    value=_DEFAULTS.host,
                    id="host",
                    placeholder="FreeIPA host",
                )
                yield Label("Username")
                yield Input(
                    value=_DEFAULTS.username,
                    id="username",
                    placeholder="Username",
                )
                yield Label("Password")
                yield Input(
                    password=True,
                    id="password",
                    placeholder="Password",
                )
                yield Button("Login", id="login-btn", variant="primary")
                yield Static("", id="login-error")

    def on_mount(self) -> None:
        self.query_one("#password", Input).focus()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "login-btn":
            self._do_login()

    def on_input_submitted(self, event: Input.Submitted) -> None:
        self._do_login()

    @work(thread=True)
    def _do_login(self) -> None:
        host = self.query_one("#host", Input).value.strip()
        username = self.query_one("#username", Input).value.strip()
        password = self.query_one("#password", Input).value

        if not all([host, username, password]):
            self.app.call_from_thread(self._show_error, "All fields are required")
            return

        config = IPAConfig(host=host, username=username)
        client = IPAClient(config)

        self.app.call_from_thread(self._show_error, "Connecting...")

        try:
            my_info = client.login(password)
        except Exception as e:
            self.app.call_from_thread(self._show_error, f"Login failed: {e}")
            return

        self.app.call_from_thread(self._on_login_success, client, my_info)

    def _show_error(self, message: str) -> None:
        self.query_one("#login-error", Static).update(message)

    def _on_login_success(self, client: IPAClient, my_info: dict) -> None:
        self.app.ipa_client = client
        self.app.my_info = my_info
        from ipa_tui.screens.main import MainScreen
        self.app.switch_screen(MainScreen())
