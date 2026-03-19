# ipa-tui

Terminal client for FreeIPA with interactive TUI and CLI.

Built with [Textual](https://github.com/Textualize/textual) and [python-freeipa](https://github.com/opennode/python-freeipa).

![Python 3.12+](https://img.shields.io/badge/python-3.12%2B-blue)

## Features

- **TUI** — interactive interface with sections: users, groups, HBAC rules, sudo rules
- **CLI** — quick commands to query FreeIPA data
- **Authentication** — three-tier chain: session cache → macOS Keychain → interactive prompt
- **JSON output** — `--json` flag for scripting and piping

## Installation

Requires Python 3.12+ and [uv](https://docs.astral.sh/uv/).

```bash
git clone <repo-url>
cd ipa-tui
uv run ipa-tui
```

Or install globally:

```bash
uv tool install .
ipa-tui
```

## Configuration

Set environment variables:

| Variable | Description | Default |
|----------|-------------|---------|
| `IPA_HOST` | FreeIPA server hostname | `ipa.example.local` |
| `IPA_USER` | Username | `$USER` |
| `IPA_VERIFY_SSL` | Verify SSL certificate | `true` |

Example:

```bash
export IPA_HOST="ipa.corp.local"
export IPA_USER="admin"
export IPA_VERIFY_SSL="false"   # for self-signed certificates
```

Or pass via CLI flags:

```bash
ipa-tui --host ipa.corp.local --login admin
```

## Usage

### TUI (interactive mode)

```bash
ipa-tui           # or
ipa-tui tui
```

Keybindings:

| Key | Action |
|-----|--------|
| `/` | Open search/filter |
| `Enter` | Open details / submit search |
| `Escape` | Go back |
| `r` | Refresh current section |
| `q` | Quit |

Sections:
- **My Info** — current user attributes
- **Groups** — all groups with local filtering
- **Users** — search users (queries API on Enter)
- **HBAC Rules** — Host-Based Access Control rules
- **Sudo Rules** — sudo rules

### CLI commands

```bash
ipa-tui user <uid>              # user details
ipa-tui user-groups <uid>       # user group memberships (direct + indirect)
ipa-tui user-search <query>     # search users
ipa-tui group <name>            # group details
ipa-tui group-members <name>    # group members
ipa-tui hbac [name]             # list or show HBAC rules
ipa-tui sudo [name]             # list or show sudo rules
ipa-tui whoami                  # current user info
```

### Session management

```bash
ipa-tui login                   # login and save password to Keychain
ipa-tui logout                  # clear session cache and Keychain entry
```

### JSON output

Add `--json` **before** the subcommand:

```bash
ipa-tui --json user admin
ipa-tui --json group admins | jq '.member_user'
ipa-tui --json user-groups admin | jq '.direct'
```

## Authentication

Three-tier authentication chain:

1. **Session cache** — `~/.cache/ipa-tui/session.json`, cookie valid for ~20 minutes
2. **macOS Keychain** — auto-login with stored password
3. **Interactive prompt** — asks for password, offers to save to Keychain

Session cache is stored with `0600` permissions.

> **Why no API token?** FreeIPA doesn't support token-based auth — it uses password authentication via JSON-RPC and returns a session cookie. Password is only needed on first login, then session cache and Keychain take over.

## License

MIT
