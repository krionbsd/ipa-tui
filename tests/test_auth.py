import json
import time

from ipa_tui import auth


def test_save_and_load_session(tmp_path, monkeypatch):
    session_file = tmp_path / "session.json"
    monkeypatch.setattr(auth, "CACHE_DIR", tmp_path)
    monkeypatch.setattr(auth, "SESSION_FILE", session_file)

    auth.save_session("ipa.test.local", {"ipa_session": "abc123"})

    assert session_file.exists()
    assert oct(session_file.stat().st_mode & 0o777) == "0o600"

    cookies = auth.load_session("ipa.test.local")
    assert cookies == {"ipa_session": "abc123"}


def test_load_session_wrong_host(tmp_path, monkeypatch):
    session_file = tmp_path / "session.json"
    monkeypatch.setattr(auth, "CACHE_DIR", tmp_path)
    monkeypatch.setattr(auth, "SESSION_FILE", session_file)

    auth.save_session("ipa.test.local", {"ipa_session": "abc123"})
    assert auth.load_session("other.host") is None


def test_load_session_expired(tmp_path, monkeypatch):
    session_file = tmp_path / "session.json"
    monkeypatch.setattr(auth, "CACHE_DIR", tmp_path)
    monkeypatch.setattr(auth, "SESSION_FILE", session_file)

    data = {
        "host": "ipa.test.local",
        "cookies": {"ipa_session": "abc123"},
        "timestamp": time.time() - 9999,
    }
    session_file.write_text(json.dumps(data))

    assert auth.load_session("ipa.test.local", max_age=60) is None


def test_load_session_missing(tmp_path, monkeypatch):
    monkeypatch.setattr(auth, "SESSION_FILE", tmp_path / "nonexistent.json")
    assert auth.load_session("ipa.test.local") is None


def test_clear_session(tmp_path, monkeypatch):
    session_file = tmp_path / "session.json"
    monkeypatch.setattr(auth, "CACHE_DIR", tmp_path)
    monkeypatch.setattr(auth, "SESSION_FILE", session_file)

    auth.save_session("ipa.test.local", {"ipa_session": "abc123"})
    assert session_file.exists()

    auth.clear_session()
    assert not session_file.exists()


def test_clear_session_already_missing(tmp_path, monkeypatch):
    monkeypatch.setattr(auth, "SESSION_FILE", tmp_path / "nonexistent.json")
    auth.clear_session()


def test_load_session_corrupted(tmp_path, monkeypatch):
    session_file = tmp_path / "session.json"
    monkeypatch.setattr(auth, "SESSION_FILE", session_file)
    session_file.write_text("not json")
    assert auth.load_session("ipa.test.local") is None
