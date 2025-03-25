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

from eaclient import exceptions, gpg
from eaclient.testing import helpers


class TestExportGPGKey:
    @pytest.mark.parametrize(
        ["source_exists", "expected_raises"],
        [
            (True, helpers.does_not_raise()),
            (False, pytest.raises(exceptions.GPGKeyNotFound)),
        ],
    )
    @mock.patch("eaclient.gpg.shutil.copy")
    @mock.patch("eaclient.gpg.os.chmod")
    @mock.patch("eaclient.gpg.os.path.exists")
    def test_export_gpg_key(
        self,
        m_exists,
        m_chmod,
        m_copy,
        source_exists,
        expected_raises,
    ):
        m_exists.return_value = source_exists
        with expected_raises:
            gpg.export_gpg_key(mock.sentinel.source, mock.sentinel.dest)
            assert m_copy.call_args_list == [
                mock.call(mock.sentinel.source, mock.sentinel.dest)
            ]
            assert m_chmod.call_args_list == [
                mock.call(mock.sentinel.dest, 0o644)
            ]
