from __future__ import annotations

from textual.widgets import Tree


SECTIONS = {
    "my_info": "My Info",
    "groups": "Groups",
    "users": "Users",
    "hbac_rules": "HBAC Rules",
    "sudo_rules": "Sudo Rules",
}


class NavigationTree(Tree):
    def __init__(self) -> None:
        super().__init__("FreeIPA", id="nav-tree")

    def on_mount(self) -> None:
        self.root.expand()
        for key, label in SECTIONS.items():
            self.root.add_leaf(label, data=key)
        self.show_root = False
