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

from eaclient import messages

from eaclient.cli.commands import ProCommand


def action_help(args, **kwargs):
    # Avoiding a circular import
    from eaclient.cli import get_parser
    get_parser().print_help()

    return 0


help_command = ProCommand(
    "help",
    help=messages.CLI_ROOT_HELP,
    description=messages.CLI_HELP_DESC,
    action=action_help,
)
