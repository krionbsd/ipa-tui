from __future__ import annotations

import urllib3
from python_freeipa import ClientMeta
from python_freeipa.exceptions import FreeIPAError

from ipa_tui import auth
from ipa_tui.config import IPAConfig

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


class IPAClient:
    def __init__(self, config: IPAConfig):
        self._config = config
        self._client: ClientMeta | None = None
        self._password: str | None = None

    def _make_client(self) -> ClientMeta:
        return ClientMeta(self._config.host, verify_ssl=self._config.verify_ssl)

    def login(self, password: str) -> dict:
        self._password = password
        self._client = self._make_client()
        self._client.login(self._config.username, password)
        self._save_session()
        return self.get_my_info()

    def login_cached(self) -> bool:
        cookies = auth.load_session(self._config.host)
        if not cookies:
            return False
        self._client = self._make_client()
        for name, value in cookies.items():
            self._client._session.cookies.set(name, value)
        self._client._current_host = self._config.host
        try:
            self.get_my_info()
            return True
        except Exception:
            auth.clear_session()
            return False

    def _save_session(self):
        if self._client:
            cookies = dict(self._client._session.cookies)
            auth.save_session(self._config.host, cookies)

    def _reconnect(self):
        if self._client and self._password:
            self._client.login(self._config.username, self._password)
            self._save_session()

    def _call(self, method: str, *args, **kwargs):
        fn = getattr(self._client, method)
        try:
            return fn(*args, **kwargs)
        except FreeIPAError as e:
            if "401" in str(e) or "Unauthorized" in str(e):
                self._reconnect()
                return fn(*args, **kwargs)
            raise

    @staticmethod
    def _extract_list(result) -> list[dict]:
        if isinstance(result, list):
            return result
        if isinstance(result, dict):
            inner = result.get("result")
            if isinstance(inner, list):
                return inner
        return []

    @staticmethod
    def _extract_dict(result) -> dict:
        if isinstance(result, dict) and "result" in result:
            inner = result["result"]
            if isinstance(inner, dict):
                return inner
        return result if isinstance(result, dict) else {}

    def get_my_info(self) -> dict:
        result = self._call("user_show", a_uid=self._config.username, o_all=True)
        return self._extract_dict(result)

    def list_groups(self, criteria: str = "") -> list[dict]:
        result = self._call("group_find", a_criteria=criteria, o_sizelimit=0, o_all=False)
        return self._extract_list(result)

    def show_group(self, cn: str) -> dict:
        return self._extract_dict(self._call("group_show", a_cn=cn, o_all=True))

    def search_users(self, criteria: str) -> list[dict]:
        result = self._call("user_find", a_criteria=criteria, o_sizelimit=50, o_all=False)
        return self._extract_list(result)

    def show_user(self, uid: str) -> dict:
        return self._extract_dict(self._call("user_show", a_uid=uid, o_all=True))

    def list_hbac_rules(self, criteria: str = "") -> list[dict]:
        result = self._call("hbacrule_find", a_criteria=criteria, o_sizelimit=0, o_all=False)
        return self._extract_list(result)

    def show_hbac_rule(self, cn: str) -> dict:
        return self._extract_dict(self._call("hbacrule_show", a_cn=cn, o_all=True))

    def list_sudo_rules(self, criteria: str = "") -> list[dict]:
        result = self._call("sudorule_find", a_criteria=criteria, o_sizelimit=0, o_all=False)
        return self._extract_list(result)

    def show_sudo_rule(self, cn: str) -> dict:
        return self._extract_dict(self._call("sudorule_show", a_cn=cn, o_all=True))
