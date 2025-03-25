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

from eaclient.cli.validate import test_command

from eaclient.exceptions import ConnectivityError


class TestAction:
    @mock.patch("eaclient.lock.check_lock_info", return_value=(-1, ""))
    @mock.patch("eaclient.actions.action_to_request")
    def test_validate_with_token_success(
        self, mock_action_to_request, FakeConfig
    ):
        """Test successful connection with token to API Server"""
        args = mock.MagicMock(
            token="valid-token", attach_config=None
        )
        cfg = FakeConfig()
        ret = test_command.action(args, cfg=cfg)

        mock_action_to_request.assert_called_once_with(
            cfg, cmd="test", token="valid-token"
        )
        assert ret == 0

    @mock.patch("eaclient.lock.check_lock_info", return_value=(-1, ""))
    @mock.patch("eaclient.actions.action_to_request")
    def test_validate_without_token_success(
        self, mock_action_to_request, FakeConfig
    ):
        """Test successful connection with token to API Server"""
        args = mock.MagicMock(
            token=None, attach_config=None
        )
        cfg = FakeConfig()
        ret = test_command.action(args, cfg=cfg)

        mock_action_to_request.assert_called_once_with(
            cfg, cmd="test", token=None
        )
        assert ret == 0

    @mock.patch("eaclient.lock.check_lock_info", return_value=(-1, ""))
    @mock.patch("eaclient.actions.action_to_request")
    def test_validate_fails_on_connectivity_error(
        self, mock_action_to_request, FakeConfig
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
            test_command.action(args, cfg=cfg)

        assert e.value.code == 1
