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

import json

import mock
import pytest

from eaclient import event_logger, lock, messages
from eaclient.cli import main_error_handler
from eaclient.cli.join import join_command
from eaclient.data_types import AttachActionsConfigFile
from eaclient.exceptions import (
    AlreadyAttachedError,
    LockHeldError,
    NonRootUserError,
    ELxrProError,
    CLIAttachTokenArgORConfigRequired,
    ConnectivityError,
)
from eaclient.testing.fakes import FakeFile


BASIC_MACHINE_TOKEN = {
    "machineId": "test_machine_id",
    "token": "non-empty-token",
    "machineInfo": {
        "distribution": "elxr12",
        "kernel": "6.1.123",
        "series": "aria-updates",
        "architecture": "x86_64",
        "desktop": False,
        "virt": None,
        "clientVersion": "1.0.0"
    },
}


@mock.patch(
    "eaclient.cli.cli_util.util.we_are_currently_root", return_value=False
)
def test_non_root_users_are_rejected(
    m_we_are_currently_root, FakeConfig, capsys, event
):
    """Check that a UID != 0 will receive a message and exit non-zero"""

    cfg = FakeConfig()
    with pytest.raises(NonRootUserError):
        join_command.action(mock.MagicMock(), cfg)

    with pytest.raises(SystemExit):
        with mock.patch.object(
            event, "_event_logger_mode", event_logger.EventLoggerMode.JSON
        ):
            main_error_handler(join_command.action)(mock.MagicMock(), cfg)

    expected = {

        "errors": [
            {
                "message": messages.E_NONROOT_USER.msg,
                "message_code": messages.E_NONROOT_USER.name,
                "service": None,
                "type": "system",
            }
        ],
        "result": "failure",
        "warnings": [],
    }
    filtered = json.loads(capsys.readouterr()[0])
    filtered.pop("environment_vars", None)
    assert expected == filtered


class TestActionAttach:
    def test_already_attached(self, capsys, fake_machine_token_file, event):
        """Check that an already-attached machine emits message and exits 0"""
        fake_machine_token_file.attached = True

        with pytest.raises(AlreadyAttachedError):
            join_command.action(mock.MagicMock(), cfg=None)

        with pytest.raises(SystemExit):
            with mock.patch.object(
                event, "_event_logger_mode", event_logger.EventLoggerMode.JSON
            ):
                main_error_handler(join_command.action)(
                    mock.MagicMock(), None
                )

        msg = messages.E_ALREADY_ATTACHED.format(
            account_name="not-full"
        )
        expected = {
            "errors": [
                {
                    "additional_info": {"account_name": "not-full"},
                    "message": msg.msg,
                    "message_code": msg.name,
                    "service": None,
                    "type": "system",
                }
            ],
            "result": "failure",
            "warnings": [],
        }
        filtered = json.loads(capsys.readouterr()[0])
        filtered.pop("environment_vars", None)
        assert expected == filtered

    @mock.patch("eaclient.lock.check_lock_info")
    @mock.patch("time.sleep")
    @mock.patch("eaclient.system.subp")
    def test_lock_file_exists(
        self,
        m_subp,
        m_sleep,
        m_check_lock_info,
        capsys,
        FakeConfig,
        event,
    ):
        cfg = FakeConfig()
        m_check_lock_info.return_value = (123, "elxr-pro leave")
        expected_msg = messages.E_LOCK_HELD_ERROR.format(
            lock_request="elxr-pro join", lock_holder="elxr-pro leave", pid=123
        )
        """Check when an operation holds a lock file, attach cannot run."""
        with pytest.raises(LockHeldError) as exc_info:
            join_command.action(mock.MagicMock(), cfg=cfg)
        assert 12 == m_check_lock_info.call_count
        assert expected_msg.msg == exc_info.value.msg

        with pytest.raises(SystemExit):
            with mock.patch.object(
                event, "_event_logger_mode", event_logger.EventLoggerMode.JSON
            ):
                main_error_handler(join_command.action)(
                    mock.MagicMock(), cfg
                )

        expected = {
            "result": "failure",
            "errors": [
                {
                    "additional_info": {
                        "lock_holder": "elxr-pro leave",
                        "lock_request": "elxr-pro join",
                        "pid": 123,
                    },
                    "message": expected_msg.msg,
                    "message_code": expected_msg.name,
                    "service": None,
                    "type": "system",
                }
            ],
            "warnings": [],
        }
        filtered = json.loads(capsys.readouterr()[0])
        filtered.pop("environment_vars", None)
        assert expected == filtered

    @mock.patch("eaclient.lock.check_lock_info", return_value=(-1, ""))
    def test_attach_config_and_token_mutually_exclusive(
        self,
        FakeConfig,
    ):
        args = mock.MagicMock(
            token="something", attach_config=FakeFile("something")
        )
        cfg = FakeConfig()
        with pytest.raises(ELxrProError) as e:
            with mock.patch.object(lock, "lock_data_file"):
                join_command.action(args, cfg=cfg)

        assert e.value.msg == messages.E_ATTACH_TOKEN_ARG_XOR_CONFIG.msg

    @mock.patch("eaclient.lock.check_lock_info", return_value=(-1, ""))
    def test_attach_requires_token_or_config(self, FakeConfig):
        """Test that either token or attach_config must be provided"""
        args = mock.MagicMock(token=None, attach_config=None)
        cfg = FakeConfig()

        with pytest.raises(CLIAttachTokenArgORConfigRequired) as e:
            with mock.patch.object(lock, "lock_data_file"):
                join_command.action(args, cfg=cfg)

        assert e.value.msg == \
            messages.E_ATTACH_TOKEN_ARG_OR_CONFIG_REQUIRED.msg

    @mock.patch("eaclient.system.write_file")
    @mock.patch("eaclient.lock.check_lock_info", return_value=(-1, ""))
    @mock.patch("eaclient.actions.action_to_request")
    def test_attach_with_token_success(
        self,
        mock_action_to_request,
        mock_check_lock_info,
        mock_write_file,
        FakeConfig
    ):
        """Test successful attachment when a valid token is provided"""
        args = mock.MagicMock(
            token="valid-token", attach_config=None, pro_only=True
        )
        cfg = FakeConfig()

        ret = join_command.action(args, cfg=cfg)

        mock_action_to_request.assert_called_once_with(
            cfg, cmd="join", token="valid-token", pro_only_enable=True,
        )
        assert ret == 0

    @mock.patch("eaclient.system.write_file")
    @mock.patch("eaclient.lock.check_lock_info", return_value=(-1, ""))
    @mock.patch("eaclient.actions.action_to_request")
    def test_attach_with_attach_config_success(
        self, mock_action_to_request, mock_write_file, FakeConfig
    ):
        """Test successful attachment when attach_config is provided"""
        fake_config_content = '{"token": "config-token"}'
        args = mock.MagicMock(
            token=None,
            attach_config=FakeFile(fake_config_content),
            pro_only=False,
        )
        cfg = FakeConfig()

        with mock.patch(
            "eaclient.data_types.AttachActionsConfigFile.from_dict"
        ) as mock_from_dict:
            mock_from_dict.return_value = AttachActionsConfigFile(
                token="config-token"
            )

            ret = join_command.action(args, cfg=cfg)

        mock_action_to_request.assert_called_once_with(
            cfg, cmd="join", token="config-token", pro_only_enable=False,
        )
        assert ret == 0

    @mock.patch("eaclient.system.write_file")
    @mock.patch("eaclient.lock.check_lock_info", return_value=(-1, ""))
    @mock.patch("eaclient.actions.action_to_request")
    def test_attach_fails_on_connectivity_error(
        self, mock_action_to_request, mock_write_file, FakeConfig
    ):
        """Test failure due to network connectivity error"""
        cause = Exception("Simulated connectivity issue")
        side_effect = ConnectivityError(
            cause=cause, url="https://contract.server"
        )
        mock_action_to_request.side_effect = side_effect

        args = mock.MagicMock(token="valid-token", attach_config=None)
        cfg = FakeConfig()

        with pytest.raises(SystemExit) as e:
            join_command.action(args, cfg=cfg)

        assert e.value.code == 1
