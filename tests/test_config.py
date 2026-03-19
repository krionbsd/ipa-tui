import os

from ipa_tui.config import IPAConfig


def test_config_defaults():
    config = IPAConfig()
    assert isinstance(config.host, str)
    assert isinstance(config.username, str)
    assert isinstance(config.verify_ssl, bool)


def test_config_from_env(monkeypatch):
    monkeypatch.setenv("IPA_HOST", "ipa.test.local")
    monkeypatch.setenv("IPA_USER", "testuser")
    monkeypatch.setenv("IPA_VERIFY_SSL", "false")
    config = IPAConfig()
    assert config.host == "ipa.test.local"
    assert config.username == "testuser"
    assert config.verify_ssl is False
