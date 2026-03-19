from __future__ import annotations

import json
import subprocess
import time
from pathlib import Path

CACHE_DIR = Path.home() / ".cache" / "ipa-tui"
SESSION_FILE = CACHE_DIR / "session.json"
KEYCHAIN_SERVICE = "ipa-tui"


def _ensure_cache_dir():
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    SESSION_FILE.chmod(0o600) if SESSION_FILE.exists() else None


def save_session(host: str, cookies: dict):
    _ensure_cache_dir()
    data = {
        "host": host,
        "cookies": cookies,
        "timestamp": time.time(),
    }
    SESSION_FILE.write_text(json.dumps(data))
    SESSION_FILE.chmod(0o600)


def load_session(host: str, max_age: int = 1200) -> dict | None:
    if not SESSION_FILE.exists():
        return None
    try:
        data = json.loads(SESSION_FILE.read_text())
        if data.get("host") != host:
            return None
        if time.time() - data.get("timestamp", 0) > max_age:
            return None
        return data.get("cookies")
    except (json.JSONDecodeError, KeyError):
        return None


def clear_session():
    if SESSION_FILE.exists():
        SESSION_FILE.unlink()


def keychain_set(account: str, password: str):
    subprocess.run(
        [
            "security",
            "add-generic-password",
            "-U",
            "-s",
            KEYCHAIN_SERVICE,
            "-a",
            account,
            "-w",
            password,
        ],
        check=True,
        capture_output=True,
    )


def keychain_get(account: str) -> str | None:
    try:
        result = subprocess.run(
            [
                "security",
                "find-generic-password",
                "-s",
                KEYCHAIN_SERVICE,
                "-a",
                account,
                "-w",
            ],
            check=True,
            capture_output=True,
            text=True,
        )
        return result.stdout.strip()
    except subprocess.CalledProcessError:
        return None


def keychain_delete(account: str):
    try:
        subprocess.run(
            [
                "security",
                "delete-generic-password",
                "-s",
                KEYCHAIN_SERVICE,
                "-a",
                account,
            ],
            capture_output=True,
        )
    except subprocess.CalledProcessError:
        pass
