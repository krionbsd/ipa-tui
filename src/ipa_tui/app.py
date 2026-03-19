from __future__ import annotations

from textual.app import App

from ipa_tui.client import IPAClient
from ipa_tui.screens.login import LoginScreen


class IPAApp(App):
    TITLE = "FreeIPA TUI"

    ipa_client: IPAClient | None = None
    my_info: dict | None = None

    def on_mount(self) -> None:
        self.push_screen(LoginScreen())


def main():
    app = IPAApp()
    app.run()


if __name__ == "__main__":
    main()
