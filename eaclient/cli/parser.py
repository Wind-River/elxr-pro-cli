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

import argparse
from collections import OrderedDict
from enum import Enum
from typing import List, NamedTuple  # noqa: F401

from eaclient import messages

HelpEntry = NamedTuple(
    "HelpEntry", [("position", int), ("name", str), ("help_string", str)]
)


class HelpCategory(Enum):

    class _Value:
        def __init__(self, code: str, msg: str):
            self.code = code
            self.msg = msg

    QUICKSTART = _Value("quickstart", messages.CLI_HELP_HEADER_QUICK_START)
    OTHER = _Value("other", messages.CLI_HELP_HEADER_OTHER)
    FLAGS = _Value("flags", messages.CLI_FLAGS)

    def __str__(self):
        return self.value.code

    @property
    def header(self):
        return self.value.msg


class ProArgumentParser(argparse.ArgumentParser):
    help_entries = OrderedDict(
        [
            (HelpCategory.QUICKSTART, []),
            (HelpCategory.OTHER, []),
            (HelpCategory.FLAGS, []),
        ]
    )  # type: OrderedDict[HelpCategory, List[HelpEntry]]

    @classmethod
    def add_help_entry(
        cls,
        category: HelpCategory,
        name: str,
        help_string: str,
        position: int = 0,
    ):
        cls.help_entries[category].append(
            HelpEntry(position=position, name=name, help_string=help_string)
        )

    def __init__(self, *args, use_main_help: bool = True, **kwargs):
        super().__init__(*args, **kwargs)
        self.use_main_help = use_main_help

    def print_help_for_command(self, command: str):
        args_list = command.split()
        args_list.append("--help")
        try:
            self.parse_args(args_list)
        # We want help for any specific command,
        # but without exiting right after
        except SystemExit:
            pass

    def format_help(self):
        if self.use_main_help:
            return super().format_help()
        help_output = self.format_usage()

        for category, items in self.help_entries.items():
            help_output += "\n"
            help_output += "{}:".format(category.header)
            help_output += "\n"

            seen = set()
            unique_items = []
            # Ensuring uniqueness based on `item.name`
            for item in sorted(items, key=lambda item: item.position):
                if item.name not in seen:
                    seen.add(item.name)
                    unique_items.append(item)

            # Formatting the help output
            for item in unique_items:
                help_output += "\n"
                help_output += "  {:<17}{}".format(item.name, item.help_string)
            help_output += "\n"

        if self.epilog:
            help_output += "\n"
            help_output += self.epilog
            help_output += "\n"

        return help_output
