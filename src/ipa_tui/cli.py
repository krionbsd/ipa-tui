from __future__ import annotations

import argparse
import getpass
import json
import sys

from ipa_tui import auth
from ipa_tui.client import IPAClient
from ipa_tui.config import IPAConfig


def _connect(args) -> IPAClient:
    config = IPAConfig(host=args.host, username=args.login)
    client = IPAClient(config)

    if not args.password:
        if client.login_cached():
            return client

    password = args.password
    if not password:
        password = auth.keychain_get(config.username)
    if not password:
        password = getpass.getpass(f"Password for {config.username}@{config.host}: ")
        save = input("Save password to macOS Keychain? [y/N]: ").strip().lower()
        if save == "y":
            auth.keychain_set(config.username, password)

    client.login(password)
    return client


def _val(v) -> str:
    if isinstance(v, list):
        return ", ".join(str(i) for i in v)
    if v is None:
        return ""
    return str(v)


def _print_fields(data: dict, fields: list[str] | None = None):
    skip = {"dn", "objectclass", "ipauniqueid"}
    for key, value in sorted(data.items()):
        if key.lower() in skip:
            continue
        if fields and key not in fields:
            continue
        print(f"{key}: {_val(value)}")


def cmd_user(args):
    client = _connect(args)
    data = client.show_user(args.uid)
    if args.json:
        json.dump(data, sys.stdout, indent=2, default=str)
        print()
    else:
        _print_fields(data)


def cmd_user_groups(args):
    client = _connect(args)
    data = client.show_user(args.uid)
    groups = data.get("memberof_group", [])
    indirect = data.get("memberofindirect_group", [])
    if args.json:
        json.dump({"direct": groups, "indirect": indirect}, sys.stdout, indent=2)
        print()
        return
    if groups:
        print("Direct groups:")
        for g in sorted(groups):
            print(f"  {g}")
    if indirect:
        print("Indirect groups:")
        for g in sorted(indirect):
            print(f"  {g}")
    if not groups and not indirect:
        print("No group memberships found")


def cmd_user_search(args):
    client = _connect(args)
    users = client.search_users(args.query)
    if args.json:
        json.dump(users, sys.stdout, indent=2, default=str)
        print()
        return
    for u in users:
        uid = _val(u.get("uid", ""))
        cn = _val(u.get("cn", ""))
        mail = _val(u.get("mail", ""))
        print(f"{uid:30s} {cn:30s} {mail}")
    print(f"\n{len(users)} users found")


def cmd_group(args):
    client = _connect(args)
    data = client.show_group(args.cn)
    if args.json:
        json.dump(data, sys.stdout, indent=2, default=str)
        print()
    else:
        _print_fields(data)


def cmd_group_members(args):
    client = _connect(args)
    data = client.show_group(args.cn)
    members = data.get("member_user", [])
    groups = data.get("member_group", [])
    if args.json:
        json.dump({"users": members, "groups": groups}, sys.stdout, indent=2)
        print()
        return
    if members:
        print("Users:")
        for m in sorted(members):
            print(f"  {m}")
    if groups:
        print("Groups:")
        for g in sorted(groups):
            print(f"  {g}")
    if not members and not groups:
        print("No members found")


def cmd_hbac(args):
    client = _connect(args)
    if args.name:
        data = client.show_hbac_rule(args.name)
        if args.json:
            json.dump(data, sys.stdout, indent=2, default=str)
            print()
        else:
            _print_fields(data)
    else:
        rules = client.list_hbac_rules()
        if args.json:
            json.dump(rules, sys.stdout, indent=2, default=str)
            print()
            return
        for r in rules:
            cn = _val(r.get("cn", ""))
            enabled = _val(r.get("ipaenabledflag", ""))
            desc = _val(r.get("description", ""))
            print(f"{cn:40s} enabled={enabled:5s} {desc}")


def cmd_sudo(args):
    client = _connect(args)
    if args.name:
        data = client.show_sudo_rule(args.name)
        if args.json:
            json.dump(data, sys.stdout, indent=2, default=str)
            print()
        else:
            _print_fields(data)
    else:
        rules = client.list_sudo_rules()
        if args.json:
            json.dump(rules, sys.stdout, indent=2, default=str)
            print()
            return
        for r in rules:
            cn = _val(r.get("cn", ""))
            enabled = _val(r.get("ipaenabledflag", ""))
            desc = _val(r.get("description", ""))
            print(f"{cn:40s} enabled={enabled:5s} {desc}")


def cmd_whoami(args):
    client = _connect(args)
    data = client.get_my_info()
    if args.json:
        json.dump(data, sys.stdout, indent=2, default=str)
        print()
    else:
        _print_fields(data)


def cmd_login(args):
    config = IPAConfig(host=args.host, username=args.login)
    password = args.password or getpass.getpass(
        f"Password for {config.username}@{config.host}: "
    )
    client = IPAClient(config)
    client.login(password)
    auth.keychain_set(config.username, password)
    print(
        f"Logged in as {config.username}. Password saved to Keychain, session cached."
    )


def cmd_logout(args):
    config = IPAConfig(host=args.host, username=args.login)
    auth.clear_session()
    auth.keychain_delete(config.username)
    print(f"Session and Keychain entry cleared for {config.username}.")


def cli_main():
    parser = argparse.ArgumentParser(prog="ipa-tui", description="FreeIPA TUI & CLI")
    defaults = IPAConfig()
    parser.add_argument("--host", default=defaults.host)
    parser.add_argument("--login", default=defaults.username)
    parser.add_argument("--password", default=None, help="password (or use prompt)")
    parser.add_argument("--json", action="store_true", help="JSON output")

    sub = parser.add_subparsers(dest="command")

    # tui (default)
    sub.add_parser("tui", help="Launch TUI")

    # user
    p = sub.add_parser("user", help="Show user details")
    p.add_argument("uid", help="User login (e.g. admin)")

    # user-groups
    p = sub.add_parser("user-groups", help="Show user group memberships")
    p.add_argument("uid", help="User login")

    # user-search
    p = sub.add_parser("user-search", help="Search users")
    p.add_argument("query", help="Search query")

    # group
    p = sub.add_parser("group", help="Show group details")
    p.add_argument("cn", help="Group name")

    # group-members
    p = sub.add_parser("group-members", help="Show group members")
    p.add_argument("cn", help="Group name")

    # hbac
    p = sub.add_parser("hbac", help="List or show HBAC rules")
    p.add_argument("name", nargs="?", help="Rule name (omit to list all)")

    # sudo
    p = sub.add_parser("sudo", help="List or show sudo rules")
    p.add_argument("name", nargs="?", help="Rule name (omit to list all)")

    # whoami
    sub.add_parser("whoami", help="Show current user info")

    # login — save password to keychain + cache session
    sub.add_parser("login", help="Login and save password to Keychain")

    # logout — clear session + keychain
    sub.add_parser("logout", help="Clear session cache and Keychain entry")

    args = parser.parse_args()

    if args.command is None or args.command == "tui":
        from ipa_tui.app import main

        main()
        return

    commands = {
        "user": cmd_user,
        "user-groups": cmd_user_groups,
        "user-search": cmd_user_search,
        "group": cmd_group,
        "group-members": cmd_group_members,
        "hbac": cmd_hbac,
        "sudo": cmd_sudo,
        "whoami": cmd_whoami,
        "login": cmd_login,
        "logout": cmd_logout,
    }

    try:
        commands[args.command](args)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
