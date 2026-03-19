import os
from dataclasses import dataclass


@dataclass
class IPAConfig:
    host: str = os.environ.get("IPA_HOST", "ipa.example.local")
    username: str = os.environ.get("IPA_USER", os.environ.get("USER", "admin"))
    verify_ssl: bool = os.environ.get("IPA_VERIFY_SSL", "true").lower() in ("true", "1", "yes")
