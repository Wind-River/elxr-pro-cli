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
import unittest
from eaclient.cli.commands import ProCommand
from eaclient.cli.help import action_help, help_command


class TestHelpCommand(unittest.TestCase):
    @mock.patch("eaclient.cli.get_parser")
    def test_action_help(self, mock_get_parser):
        mock_parser = mock.MagicMock()
        mock_get_parser.return_value = mock_parser

        result = action_help(None)

        mock_parser.print_help.assert_called_once()
        self.assertEqual(result, 0)

    def test_help_command_attributes(self):
        self.assertIsInstance(help_command, ProCommand)
        self.assertEqual(help_command.name, "help")
        self.assertEqual(help_command.action, action_help)
