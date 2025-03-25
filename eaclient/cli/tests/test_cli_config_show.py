# Copyright (c) 2025 Wind River Systems, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import mock
import pytest

from eaclient.cli import main
from eaclient.cli.config import show_subcommand
from eaclient.files.user_config_file import UserConfigData

M_PATH = "eaclient.cli."


@mock.patch("eaclient.log.setup_cli_logging")
class TestMainConfigShow:
    def test_config_show_error_on_invalid_subcommand(
        self, _m_resources, capsys, FakeConfig
    ):
        """Exit 1 on invalid subcommands."""
        with pytest.raises(SystemExit):
            with mock.patch(
                "sys.argv", ["/usr/bin/elxr-pro", "config", "invalid"]
            ):
                with mock.patch(
                    "eaclient.config.EAConfig",
                    return_value=FakeConfig(),
                ):
                    main()
        out, err = capsys.readouterr()
        assert "" == out
        expected_logs = [
            "usage: elxr-pro config [-h] {show,set,unset} ...",
            "argument command: invalid choice:"
            " 'invalid' (choose from 'show', 'set', 'unset')",
        ]
        for log in expected_logs:
            assert log in err


class TestActionConfigShow:
    @pytest.mark.parametrize(
        "optional_key",
        (
            None,
            "ea_apt_http_proxy",
            "ea_apt_https_proxy",
            None,
            None,
        ),
    )
    @mock.patch(
        "eaclient.files.user_config_file.UserConfigFileObject.read",
        return_value=UserConfigData(),
    )
    def test_show_values_and_limit_when_optional_key_provided(
        self, _m_config_read, optional_key, FakeConfig, capsys
    ):
        cfg = FakeConfig()
        cfg.user_config.ea_apt_http_proxy = "http://ea_apt_http_proxy"
        cfg.user_config.ea_apt_https_proxy = "http://ea_apt_https_proxy"
        cfg.user_config.global_apt_http_proxy = ""
        cfg.user_config.global_apt_https_proxy = ""
        args = mock.MagicMock(key=optional_key)
        show_subcommand.action(args, cfg=cfg)
        out, err = capsys.readouterr()
        if optional_key:
            assert "{key} http://{key}\n".format(key=optional_key) == out
        else:
            assert (
                """\
ea_apt_http_proxy       http://ea_apt_http_proxy
ea_apt_https_proxy      http://ea_apt_https_proxy
global_apt_http_proxy   None
global_apt_https_proxy  None
"""
                == out
            )
        assert "" == err
