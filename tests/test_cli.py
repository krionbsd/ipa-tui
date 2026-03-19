from unittest.mock import patch

from ipa_tui.cli import cli_main


def test_no_args_launches_tui():
    with patch("ipa_tui.cli.IPAConfig") as mock_cfg:
        mock_cfg.return_value.host = "ipa.test.local"
        mock_cfg.return_value.username = "testuser"
        with patch("ipa_tui.app.main") as mock_tui:
            with patch("sys.argv", ["ipa-tui"]):
                cli_main()
                mock_tui.assert_called_once()


def test_host_and_login_flags():
    with patch("ipa_tui.cli.IPAConfig") as mock_cfg:
        mock_cfg.return_value.host = "default.host"
        mock_cfg.return_value.username = "default.user"
        with patch("ipa_tui.cli.cmd_whoami") as mock_cmd:
            with patch("sys.argv", ["ipa-tui", "--host", "custom.host", "--login", "admin", "whoami"]):
                cli_main()
                args = mock_cmd.call_args[0][0]
                assert args.host == "custom.host"
                assert args.login == "admin"


def test_json_flag():
    with patch("ipa_tui.cli.IPAConfig") as mock_cfg:
        mock_cfg.return_value.host = "default.host"
        mock_cfg.return_value.username = "default.user"
        with patch("ipa_tui.cli.cmd_whoami") as mock_cmd:
            with patch("sys.argv", ["ipa-tui", "--json", "whoami"]):
                cli_main()
                args = mock_cmd.call_args[0][0]
                assert args.json is True
