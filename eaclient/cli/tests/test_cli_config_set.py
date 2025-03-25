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

from eaclient import apt, http, messages
from eaclient.cli import main
from eaclient.cli.cli_util import configure_apt_proxy
from eaclient.cli.config import set_subcommand
from eaclient.exceptions import NonRootUserError


@mock.patch("eaclient.log.setup_cli_logging")
class TestMainConfigSet:
    @pytest.mark.parametrize(
        "kv_pair,err_msg",
        (
            ("junk", "\nExpected <key>=<value> but found: junk\n"),
            (
                "k=v",
                "<key> must be one of: ea_apt_http_proxy, ea_apt_https_proxy,"
                " global_apt_http_proxy, global_apt_https_proxy"
            ),
            (
                "http_proxys=",
                "<key> must be one of: ea_apt_http_proxy, ea_apt_https_proxy,"
                " global_apt_http_proxy, global_apt_https_proxy"
            ),
            (
                "=value",
                "<key> must be one of: ea_apt_http_proxy, ea_apt_https_proxy,"
                " global_apt_http_proxy, global_apt_https_proxy"
            ),
            (
                "global_apt_http_proxy=",
                "Empty value provided for global_apt_http_proxy.",
            ),
            (
                "global_apt_https_proxy=  ",
                "Empty value provided for global_apt_https_proxy.",
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
                "sys.argv", ["/usr/bin/elxr-pro", "config", "set", kv_pair]
            ):
                with mock.patch(
                    "eaclient.config.EAConfig",
                    return_value=FakeConfig(),
                ):
                    main()
        out, err = capsys.readouterr()
        assert err_msg in err


@mock.patch("eaclient.config.user_config_file.user_config.write")
class TestActionConfigSet:
    @mock.patch("eaclient.util.we_are_currently_root", return_value=False)
    def test_set_error_on_non_root_user(
        self,
        _m_resources,
        _we_are_currently_root,
        FakeConfig,
    ):
        """Root is required to run pro config set."""
        args = mock.MagicMock(key_value_pair="something=1")
        cfg = FakeConfig()
        with pytest.raises(NonRootUserError):
            set_subcommand.action(args, cfg=cfg)

    @pytest.mark.parametrize(
        "key,value,scope,protocol_type",
        (
            (
                "global_apt_http_proxy",
                "http://proxy",
                apt.AptProxyScope.GLOBAL,
                "http",
            ),
            (
                "global_apt_https_proxy",
                "https://proxy",
                apt.AptProxyScope.GLOBAL,
                "https",
            ),
        ),
    )
    @mock.patch("eaclient.cli.cli_util.configure_apt_proxy")
    @mock.patch("eaclient.http.validate_proxy")
    def test_set_apt_http_proxy_and_apt_https_proxy_prints_warning(
        self,
        validate_proxy,
        configure_apt_proxy,
        _m_resources,
        key,
        value,
        scope,
        protocol_type,
        FakeConfig,
        capsys,
    ):
        """Set calls setup_apt_proxy but prints warning"""
        args = mock.MagicMock(key_value_pair="{}={}".format(key, value))
        cfg = FakeConfig()
        set_subcommand.action(args, cfg=cfg)
        out, err = capsys.readouterr()
        assert [
            mock.call(cfg, apt.AptProxyScope.GLOBAL, key, value)
        ] == configure_apt_proxy.call_args_list

        proxy_type = key.replace("global_apt_", "")
        if proxy_type == "http_proxy":
            url = http.PROXY_VALIDATION_APT_HTTP_URL
        else:
            url = http.PROXY_VALIDATION_APT_HTTPS_URL
        assert [
            mock.call(proxy_type.replace("_proxy", ""), value, url)
        ] == validate_proxy.call_args_list

        assert getattr(cfg, key) == value
        assert cfg.ea_apt_https_proxy is None
        assert cfg.ea_apt_http_proxy is None

    @pytest.mark.parametrize(
        "key,value,scope,apt_equ,ea_apt_equ",
        (
            (
                "global_apt_http_proxy",
                "http://proxy",
                apt.AptProxyScope.GLOBAL,
                None,
                None,
            ),
            (
                "global_apt_https_proxy",
                "https://proxy",
                apt.AptProxyScope.GLOBAL,
                "https://proxy",
                None,
            ),
            (
                "global_apt_http_proxy",
                "https://proxy",
                apt.AptProxyScope.GLOBAL,
                "https://proxy",
                None,
            ),
            (
                "global_apt_http_proxy",
                "https://proxy",
                apt.AptProxyScope.GLOBAL,
                None,
                "https://proxy",
            ),
            (
                "global_apt_https_proxy",
                "https://proxy",
                apt.AptProxyScope.GLOBAL,
                None,
                "https://proxy",
            ),
            (
                "global_apt_https_proxy",
                "https://proxy",
                apt.AptProxyScope.GLOBAL,
                "https://proxy",
                "https://proxy",
            ),
            (
                "global_apt_http_proxy",
                "https://proxy",
                apt.AptProxyScope.GLOBAL,
                "https://proxy",
                "https://proxy",
            ),
        ),
    )
    @mock.patch("eaclient.cli.cli_util.configure_apt_proxy")
    @mock.patch("eaclient.http.validate_proxy")
    def test_set_global_apt_http_and_global_apt_https_proxy(
        self,
        validate_proxy,
        configure_apt_proxy,
        _m_resources,
        key,
        value,
        scope,
        apt_equ,
        ea_apt_equ,
        FakeConfig,
        capsys,
    ):
        """Test setting of global_apt_* proxies"""
        args = mock.MagicMock(key_value_pair="{}={}".format(key, value))
        cfg = FakeConfig()
        cfg.ea_apt_https_proxy = ea_apt_equ
        cfg.ea_apt_http_proxy = ea_apt_equ
        set_subcommand.action(args, cfg=cfg)
        out, err = capsys.readouterr()  # will need to check output
        if ea_apt_equ:
            assert [
                mock.call(cfg, scope, key, value)
            ] == configure_apt_proxy.call_args_list
            assert (
                messages.WARNING_APT_PROXY_OVERWRITE.format(
                    current_proxy="global apt", previous_proxy="pro scoped apt"
                )
                in out
            )
        else:
            assert [
                mock.call(cfg, apt.AptProxyScope.GLOBAL, key, value)
            ] == configure_apt_proxy.call_args_list

        proxy_type = key.replace("global_apt_", "")
        if proxy_type == "http_proxy":
            url = http.PROXY_VALIDATION_APT_HTTP_URL
        else:
            url = http.PROXY_VALIDATION_APT_HTTPS_URL
        assert [
            mock.call(proxy_type.replace("_proxy", ""), value, url)
        ] == validate_proxy.call_args_list
        assert cfg.ea_apt_https_proxy is None
        assert cfg.ea_apt_http_proxy is None

    @pytest.mark.parametrize(
        "key,value,scope,apt_equ,global_apt_equ",
        (
            (
                "ea_apt_http_proxy",
                "http://proxy",
                apt.AptProxyScope.EACLIENT,
                None,
                None,
            ),
            (
                "ea_apt_https_proxy",
                "http://proxy",
                apt.AptProxyScope.EACLIENT,
                "https://proxy",
                "https://proxy",
            ),
            (
                "ea_apt_https_proxy",
                "http://proxy",
                apt.AptProxyScope.EACLIENT,
                "https://proxy",
                None,
            ),
            (
                "ea_apt_http_proxy",
                "http://proxy",
                apt.AptProxyScope.EACLIENT,
                "https://proxy",
                None,
            ),
            (
                "ea_apt_https_proxy",
                "http://proxy",
                apt.AptProxyScope.EACLIENT,
                None,
                "https://proxy",
            ),
            (
                "ea_apt_http_proxy",
                "http://proxy",
                apt.AptProxyScope.EACLIENT,
                None,
                "https://proxy",
            ),
            (
                "ea_apt_http_proxy",
                "http://proxy",
                apt.AptProxyScope.EACLIENT,
                "https://proxy",
                "https://proxy",
            ),
        ),
    )
    @mock.patch("eaclient.cli.cli_util.configure_apt_proxy")
    @mock.patch("eaclient.http.validate_proxy")
    def test_set_ea_apt_http_and_ea_apt_https_proxy(
        self,
        validate_proxy,
        configure_apt_proxy,
        _m_resources,
        key,
        value,
        scope,
        apt_equ,
        global_apt_equ,
        FakeConfig,
        capsys,
    ):
        """Test setting of ea_apt_* proxies"""
        args = mock.MagicMock(key_value_pair="{}={}".format(key, value))
        cfg = FakeConfig()
        cfg.global_apt_http_proxy = global_apt_equ
        cfg.global_apt_https_proxy = global_apt_equ
        set_subcommand.action(args, cfg=cfg)
        out, err = capsys.readouterr()  # will need to check output
        if global_apt_equ:
            assert [
                mock.call(cfg, scope, key, value)
            ] == configure_apt_proxy.call_args_list
            assert (
                messages.WARNING_APT_PROXY_OVERWRITE.format(
                    current_proxy="pro scoped apt", previous_proxy="global apt"
                )
                in out
            )
        else:
            assert [
                mock.call(cfg, apt.AptProxyScope.EACLIENT, key, value)
            ] == configure_apt_proxy.call_args_list

        proxy_type = key.replace("ea_apt_", "")
        if proxy_type == "http_proxy":
            url = http.PROXY_VALIDATION_APT_HTTP_URL
        else:
            url = http.PROXY_VALIDATION_APT_HTTPS_URL
        assert [
            mock.call(proxy_type.replace("_proxy", ""), value, url)
        ] == validate_proxy.call_args_list
        assert cfg.global_apt_https_proxy is None
        assert cfg.global_apt_http_proxy is None

    @pytest.mark.parametrize(
        "key,value,scope",
        (
            (
                "global_apt_https_proxy",
                "http://proxy",
                apt.AptProxyScope.GLOBAL,
            ),
            (
                "global_apt_http_proxy",
                "https://proxy",
                apt.AptProxyScope.GLOBAL,
            ),
            ("global_apt_https_proxy", None, apt.AptProxyScope.GLOBAL),
        ),
    )
    @mock.patch("eaclient.cli.cli_util.setup_apt_proxy")
    def test_configure_global_apt_proxy(
        self,
        setup_apt_proxy,
        _m_resources,
        key,
        value,
        scope,
        FakeConfig,
    ):
        cfg = FakeConfig()
        cfg.global_apt_http_proxy = value
        cfg.global_apt_https_proxy = value
        configure_apt_proxy(cfg, scope, key, value)
        kwargs = {
            "http_proxy": cfg.global_apt_http_proxy,
            "https_proxy": cfg.global_apt_https_proxy,
            "proxy_scope": scope,
        }
        assert 1 == setup_apt_proxy.call_count
        assert [mock.call(**kwargs)] == setup_apt_proxy.call_args_list

    @pytest.mark.parametrize(
        "key,value,scope",
        (
            (
                "global_apt_https_proxy",
                "http://proxy",
                apt.AptProxyScope.EACLIENT,
            ),
            (
                "global_apt_http_proxy",
                "https://proxy",
                apt.AptProxyScope.EACLIENT,
            ),
            ("global_apt_https_proxy", None, apt.AptProxyScope.EACLIENT),
        ),
    )
    @mock.patch("eaclient.cli.cli_util.setup_apt_proxy")
    def test_configure_eaclient_apt_proxy(
        self,
        setup_apt_proxy,
        _m_resources,
        key,
        value,
        scope,
        FakeConfig,
    ):
        cfg = FakeConfig()
        cfg.ea_apt_http_proxy = value
        cfg.ea_apt_https_proxy = value
        configure_apt_proxy(cfg, scope, key, value)
        kwargs = {
            "http_proxy": cfg.ea_apt_http_proxy,
            "https_proxy": cfg.ea_apt_https_proxy,
            "proxy_scope": scope,
        }
        assert 1 == setup_apt_proxy.call_count
        assert [mock.call(**kwargs)] == setup_apt_proxy.call_args_list
