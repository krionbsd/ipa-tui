import os
from dataclasses import dataclass, field


def _default_host() -> str:
    return os.environ.get("IPA_HOST", "ipa.example.local")


def _default_user() -> str:
    return os.environ.get("IPA_USER", os.environ.get("USER", "admin"))


def _default_verify_ssl() -> bool:
    return os.environ.get("IPA_VERIFY_SSL", "true").lower() in ("true", "1", "yes")


@dataclass
class IPAConfig:
    host: str = field(default_factory=_default_host)
    username: str = field(default_factory=_default_user)
    verify_ssl: bool = field(default_factory=_default_verify_ssl)
