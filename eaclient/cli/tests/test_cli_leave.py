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

from eaclient import event_logger, exceptions, lock, messages
from eaclient.cli import main_error_handler
from eaclient.cli.leave import leave_command

from eaclient.exceptions import ConnectivityError


@mock.patch("eaclient.util.prompt_for_confirmation", return_value=True)
class TestActionDetach:
    @mock.patch("eaclient.util.we_are_currently_root", return_value=False)
    def test_non_root_users_are_rejected(
        self,
        m_we_are_currently_root,
        _m_prompt,
        FakeConfig,
        fake_machine_token_file,
        event,
        capsys,
    ):
        """Check that a UID != 0 will receive a message and exit non-zero"""
        m_we_are_currently_root.return_value = False
        args = mock.MagicMock()

        cfg = FakeConfig()
        fake_machine_token_file.attached = True
        with pytest.raises(exceptions.NonRootUserError):
            leave_command.action(args, cfg=cfg)

        with pytest.raises(SystemExit):
            with mock.patch.object(
                event, "_event_logger_mode", event_logger.EventLoggerMode.JSON
            ):
                main_error_handler(leave_command.action)(args, cfg)

        expected_message = messages.E_NONROOT_USER
        expected = {
            "errors": [
                {
                    "message": expected_message.msg,
                    "message_code": expected_message.name,
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

    def test_unattached_error_message(
        self, _m_prompt, FakeConfig, capsys, event
    ):
        """Check that root user gets unattached message."""

        cfg = FakeConfig()
        args = mock.MagicMock()
        with pytest.raises(exceptions.UnattachedError) as err:
            leave_command.action(args, cfg=cfg)
        assert messages.E_UNATTACHED.msg == err.value.msg

        with pytest.raises(SystemExit):
            with mock.patch.object(
                event, "_event_logger_mode", event_logger.EventLoggerMode.JSON
            ):
                main_error_handler(leave_command.action)(args, cfg)

        expected_message = messages.E_UNATTACHED
        expected = {
            "errors": [
                {
                    "message": expected_message.msg,
                    "message_code": expected_message.name,
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
        m_prompt,
        FakeConfig,
        fake_machine_token_file,
        capsys,
        event,
    ):
        """Check when an operation holds a lock file, detach cannot run."""
        cfg = FakeConfig()
        fake_machine_token_file.attached = True
        args = mock.MagicMock()
        m_check_lock_info.return_value = (123, "pro test")

        with pytest.raises(exceptions.LockHeldError) as err:
            leave_command.action(args, cfg=cfg)

        assert 12 == m_check_lock_info.call_count
        expected_error_msg = messages.E_LOCK_HELD_ERROR.format(
            lock_request="pro leave", lock_holder="pro test", pid="123"
        )
        assert expected_error_msg.msg == err.value.msg

        with pytest.raises(SystemExit):
            with mock.patch.object(
                event, "_event_logger_mode", event_logger.EventLoggerMode.JSON
            ):
                main_error_handler(leave_command.action)(args, cfg)

        expected = {
            "errors": [
                {
                    "additional_info": {
                        "lock_holder": "pro test",
                        "lock_request": "pro leave",
                        "pid": 123,
                    },
                    "message": expected_error_msg.msg,
                    "message_code": expected_error_msg.name,
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

    @mock.patch("eaclient.lock.check_lock_info", return_value=(-1, ""))
    @mock.patch("eaclient.actions.action_to_request")
    def test_returns_zero(
        self,
        m_check_lock_info,
        m_prompt,
        FakeConfig,
        fake_machine_token_file,
        tmpdir,
    ):
        cfg = FakeConfig()
        fake_machine_token_file.attached = True
        args = mock.MagicMock()
        with mock.patch.object(lock, "lock_data_file"):
            ret = leave_command.action(args, cfg=cfg)

        assert 0 == ret

    @mock.patch("eaclient.system.write_file")
    @mock.patch("eaclient.lock.check_lock_info", return_value=(-1, ""))
    @mock.patch("eaclient.actions.action_to_request")
    def test_leave_fails_on_connectivity_error(
        self,
        mock_action_to_request,
        mock_check_lock_info,
        mock_write_file,
        FakeConfig,
        fake_machine_token_file,
    ):
        """Test failure due to network connectivity error"""
        cause = Exception("Simulated connectivity issue")
        side_effect = ConnectivityError(
            cause=cause, url="https://contract.server"
        )
        mock_action_to_request.side_effect = side_effect

        cfg = FakeConfig()
        fake_machine_token_file.attached = True
        args = mock.MagicMock()

        with pytest.raises(SystemExit) as e:
            leave_command.action(args, cfg=cfg)

        assert e.value.code == 1
