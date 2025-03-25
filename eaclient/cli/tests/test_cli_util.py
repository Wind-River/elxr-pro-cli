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

from eaclient import lock
from eaclient.cli.cli_util import (
    assert_attached,
    assert_lock_file,
    assert_not_attached,
    assert_root,
)
from eaclient.exceptions import (
    AlreadyAttachedError,
    NonRootUserError,
    UnattachedError,
)


class TestAssertLockFile:
    @mock.patch("eaclient.lock.check_lock_info", return_value=(-1, ""))
    @mock.patch("os.getpid", return_value=123)
    def test_assert_root_creates_lock_and_notice(
        self,
        _m_getpid,
        _m_check_lock_info,
        FakeConfig,
    ):
        arg, kwarg = mock.sentinel.arg, mock.sentinel.kwarg

        @assert_lock_file("some operation")
        def test_function(args, cfg):
            assert arg == mock.sentinel.arg
            assert kwarg == mock.sentinel.kwarg

            return mock.sentinel.success

        with mock.patch.object(lock, "lock_data_file") as m_lock_file:
            ret = test_function(arg, cfg=mock.MagicMock())

        assert mock.sentinel.success == ret
        assert [
            mock.call(
                lock.LockData(lock_pid="123", lock_holder="some operation")
            )
        ] == m_lock_file.write.call_args_list
        assert 1 == m_lock_file.delete.call_count


class TestAssertRoot:
    def test_assert_root_when_root(self):
        # autouse mock for we_are_currently_root defaults it to True
        arg, kwarg = mock.sentinel.arg, mock.sentinel.kwarg

        @assert_root
        def test_function(arg, *, kwarg):
            assert arg == mock.sentinel.arg
            assert kwarg == mock.sentinel.kwarg

            return mock.sentinel.success

        ret = test_function(arg, kwarg=kwarg)

        assert mock.sentinel.success == ret

    def test_assert_root_when_not_root(self):
        @assert_root
        def test_function():
            pass

        with mock.patch(
            "eaclient.cli.util.we_are_currently_root", return_value=False
        ):
            with pytest.raises(NonRootUserError):
                test_function()


# Test multiple uids, to be sure that the root checking is absent
@pytest.mark.parametrize("root", [True, False])
class TestAssertAttached:
    def test_assert_attached_when_attached(
        self, capsys, root, fake_machine_token_file
    ):
        @assert_attached()
        def test_function(args, cfg):
            return mock.sentinel.success

        fake_machine_token_file.attached = True

        with mock.patch(
            "eaclient.cli.util.we_are_currently_root", return_value=root
        ):
            ret = test_function(mock.Mock(), None)

        assert mock.sentinel.success == ret

        out, _err = capsys.readouterr()
        assert "" == out.strip()

    def test_assert_attached_when_unattached(self, root, FakeConfig):
        @assert_attached()
        def test_function(args, cfg):
            pass

        cfg = FakeConfig()

        with mock.patch(
            "eaclient.cli.util.we_are_currently_root", return_value=root
        ):
            with pytest.raises(UnattachedError):
                test_function(mock.Mock(), cfg)


@pytest.mark.parametrize("root", [True, False])
class TestAssertNotAttached:
    def test_when_attached(self, root, fake_machine_token_file):
        @assert_not_attached
        def test_function(args, cfg):
            pass

        fake_machine_token_file.attached = True

        with mock.patch(
            "eaclient.cli.util.we_are_currently_root", return_value=root
        ):
            with pytest.raises(AlreadyAttachedError):
                test_function(mock.Mock(), None)

    def test_when_not_attached(self, capsys, root, FakeConfig):
        @assert_not_attached
        def test_function(args, cfg):
            return mock.sentinel.success

        cfg = FakeConfig()

        with mock.patch(
            "eaclient.cli.util.we_are_currently_root", return_value=root
        ):
            ret = test_function(mock.Mock(), cfg)

        assert mock.sentinel.success == ret

        out, _err = capsys.readouterr()
        assert "" == out.strip()
