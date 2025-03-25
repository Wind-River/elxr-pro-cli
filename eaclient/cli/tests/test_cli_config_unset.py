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
from eaclient.cli.config import unset_subcommand
from eaclient.exceptions import NonRootUserError


@mock.patch("eaclient.log.setup_cli_logging")
class TestMainConfigUnSet:
    @pytest.mark.parametrize(
        "kv_pair,err_msg",
        (
            (
                "junk",
                "<key> must be one of: ea_apt_http_proxy, ea_apt_https_proxy,"
                " global_apt_http_proxy, global_apt_https_proxy"
            ),
            (
                "http_proxys",
                "<key> must be one of: ea_apt_http_proxy, ea_apt_https_proxy,"
                " global_apt_http_proxy, global_apt_https_proxy"
            ),
        ),
    )
    def test_set_error_with_help_on_invalid_key_value_pair(
        self,
        _m_resources,
        kv_pair,
        err_msg,
        capsys,
        FakeConfig,
        event,
    ):
        """Exit 1 and print help on invalid key_value_pair input param."""
        with pytest.raises(SystemExit):
            with mock.patch(
                "sys.argv", ["/usr/bin/elxr-pro", "config", "unset", kv_pair]
            ):
                with mock.patch(
                    "eaclient.config.EAConfig",
                    return_value=FakeConfig(),
                ):
                    main()
        out, err = capsys.readouterr()
        assert err_msg in err


@mock.patch("eaclient.config.user_config_file.user_config.write")
class TestActionConfigUnSet:
    @mock.patch("eaclient.util.we_are_currently_root", return_value=False)
    def test_set_error_on_non_root_user(
        self, we_are_currently_root, _write, FakeConfig
    ):
        """Root is required to run pro config unset."""
        args = mock.MagicMock(key="https_proxy")
        cfg = FakeConfig()
        with pytest.raises(NonRootUserError):
            unset_subcommand.action(args, cfg=cfg)
