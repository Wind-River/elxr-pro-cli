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

import contextlib
import logging
import socket

import mock
import pytest

from eaclient import defaults, exceptions, messages
from eaclient.cli import main
from eaclient.exceptions import (
    AlreadyAttachedError,
    LockHeldError,
    UnattachedError,
)

M_PATH_EACONFIG = "eaclient.config.EAConfig."


class TestMain:
    @pytest.mark.parametrize(
        "exception,expected_error_msg,expected_log",
        (
            (
                TypeError("'NoneType' object is not subscriptable"),
                messages.UNEXPECTED_ERROR.format(
                    error_msg="'NoneType' object is not subscriptable",
                    log_path="/var/log/elxr-advantage.log",
                ),
                "Unhandled exception, please file a bug",
            ),
        ),
    )
    @mock.patch("eaclient.cli.event.info")
    @mock.patch("eaclient.cli.LOG.exception")
    @mock.patch("eaclient.log.setup_cli_logging")
    @mock.patch("eaclient.cli.get_parser")
    def test_errors_handled_gracefully(
        self,
        m_get_parser,
        _m_setup_logging,
        m_log_exception,
        m_event_info,
        event,
        exception,
        expected_error_msg,
        expected_log,
        FakeConfig,
    ):
        m_args = m_get_parser.return_value.parse_args.return_value
        m_args.action.side_effect = exception

        with pytest.raises(SystemExit) as excinfo:
            with mock.patch("sys.argv", ["/usr/bin/elxr-pro", "subcmd"]):
                with mock.patch(
                    "eaclient.config.EAConfig",
                    return_value=FakeConfig(),
                ):
                    main()

        exc = excinfo.value
        print(exc.code)
        assert 1 == exc.code
        assert [
            mock.call(info_msg=expected_error_msg.msg, file_type=mock.ANY)
        ] == m_event_info.call_args_list
        assert [mock.call(expected_log)] == m_log_exception.call_args_list

    @pytest.mark.parametrize(
        "exception,expected_log",
        (
            (
                KeyboardInterrupt,
                "KeyboardInterrupt",
            ),
        ),
    )
    @mock.patch("eaclient.cli.LOG.error")
    @mock.patch("eaclient.log.setup_cli_logging")
    @mock.patch("eaclient.cli.get_parser")
    def test_interrupt_errors_handled_gracefully(
        self,
        m_get_parser,
        _m_setup_logging,
        m_log_error,
        exception,
        expected_log,
        FakeConfig,
    ):
        m_args = m_get_parser.return_value.parse_args.return_value
        m_args.action.side_effect = exception

        with pytest.raises(SystemExit) as excinfo:
            with mock.patch("sys.argv", ["/usr/bin/elxr-pro", "subcmd"]):
                with mock.patch(
                    "eaclient.config.EAConfig",
                    return_value=FakeConfig(),
                ):
                    main()

        exc = excinfo.value
        assert 1 == exc.code

        assert [mock.call(expected_log)] == m_log_error.call_args_list

    @pytest.mark.parametrize(
        "exception,expected_exit_code",
        [
            (UnattachedError(), 1),
            (AlreadyAttachedError(account_name=mock.MagicMock()), 2),
            (
                LockHeldError(
                    pid="123",
                    lock_request="elxr-pro join",
                    lock_holder="elxr-pro test",
                ),
                1,
            ),
        ],
    )
    @mock.patch("eaclient.cli.event.info")
    @mock.patch("eaclient.cli.LOG.error")
    @mock.patch("eaclient.log.setup_cli_logging")
    @mock.patch("eaclient.cli.get_parser")
    def test_user_facing_error_handled_gracefully(
        self,
        m_get_parser,
        _m_setup_logging,
        m_log_error,
        m_event_info,
        event,
        exception,
        expected_exit_code,
    ):
        m_args = m_get_parser.return_value.parse_args.return_value
        m_args.action.side_effect = exception
        expected_msg = exception.msg

        with pytest.raises(SystemExit) as excinfo:
            main(["some", "args"])

        exc = excinfo.value
        assert expected_exit_code == exc.code

        assert [
            mock.call(info_msg=expected_msg, file_type=mock.ANY)
        ] == m_event_info.call_args_list
        assert [mock.call(expected_msg)] == m_log_error.call_args_list

    @pytest.mark.parametrize(
        ["error_url", "expected_log_call"],
        (
            (
                "http://nowhere.com",
                mock.call(
                    "Failed to access URL: %s",
                    "http://nowhere.com",
                    exc_info=mock.ANY,
                ),
            ),
        ),
    )
    @mock.patch("eaclient.cli.event.info")
    @mock.patch("eaclient.cli.LOG.exception")
    @mock.patch("eaclient.log.setup_cli_logging")
    @mock.patch("eaclient.cli.get_parser")
    def test_url_error_handled_gracefully(
        self,
        m_get_parser,
        _m_setup_logging,
        m_log_exception,
        m_event_info,
        error_url,
        expected_log_call,
    ):
        m_args = m_get_parser.return_value.parse_args.return_value
        m_args.action.side_effect = exceptions.ConnectivityError(
            cause=socket.gaierror(-2, "Name or service not known"),
            url=error_url,
        )

        with pytest.raises(SystemExit) as excinfo:
            main(["some", "args"])

        exc = excinfo.value
        assert 1 == exc.code

        assert [
            mock.call(
                info_msg=messages.E_CONNECTIVITY_ERROR.format(
                    url=error_url,
                    cause_error="[Errno -2] Name or service not known",
                ).msg,
                file_type=mock.ANY,
            )
        ] == m_event_info.call_args_list
        assert [expected_log_call] == m_log_exception.call_args_list

    @pytest.mark.parametrize("caplog_text", [logging.DEBUG], indirect=True)
    @mock.patch("eaclient.log.setup_cli_logging")
    @mock.patch("eaclient.cli.get_parser")
    def test_command_line_is_logged(
        self, _m_get_parser, _m_setup_logging, caplog_text
    ):
        main(["some", "args"])

        log = caplog_text()

        assert "['some', 'args']" in log

    @pytest.mark.parametrize("caplog_text", [logging.DEBUG], indirect=True)
    @mock.patch("eaclient.log.setup_cli_logging")
    @mock.patch("eaclient.cli.get_parser")
    @mock.patch(
        "eaclient.cli.util.get_pro_environment",
        return_value={"EA_ENV": "YES", "EA_FEATURES_WOW": "XYZ"},
    )
    def test_environment_is_logged(
        self,
        _m_pro_environment,
        _m_get_parser,
        _m_setup_logging,
        caplog_text,
    ):
        main(["some", "args"])

        log = caplog_text()

        assert "EA_ENV=YES" in log
        assert "EA_FEATURES_WOW=XYZ" in log

    @mock.patch("eaclient.log.setup_cli_logging")
    @mock.patch("eaclient.cli.get_parser")
    @mock.patch("eaclient.cli.EAConfig")
    @pytest.mark.parametrize("config_error", [True, False])
    def test_setup_logging_with_defaults(
        self,
        m_config,
        _m_get_parser,
        m_setup_logging,
        config_error,
        tmpdir,
        FakeConfig,
    ):
        log_file = tmpdir.join("file.log")
        cfg = FakeConfig({"log_file": log_file.strpath})
        if not config_error:
            m_config.return_value = cfg
        else:
            m_config.side_effect = OSError("Error reading EAConfig")

        with contextlib.suppress(SystemExit):
            main(["some", "args"])

        expected_setup_logging_calls = [
            mock.call(
                defaults.CONFIG_DEFAULTS["log_level"],
                defaults.CONFIG_DEFAULTS["log_file"],
            ),
        ]

        if not config_error:
            expected_setup_logging_calls.append(
                mock.call(mock.ANY, cfg.log_file),
            )

        assert expected_setup_logging_calls == m_setup_logging.call_args_list
