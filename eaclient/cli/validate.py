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

import logging
import sys

from eaclient import (
    actions,
    config,
    event_logger,
    exceptions,
    messages,
    util,
)

from eaclient.cli.commands import ProArgument, ProArgumentGroup, ProCommand
from eaclient.cli.parser import HelpCategory


event = event_logger.get_event_logger()
LOG = logging.getLogger(util.replace_top_level_logger_name(__name__))


def action_validate(args, *, cfg, **kwargs) -> int:
    """Perform the validation of connection to for this machine.

    @return: 0 on success, 1 otherwise
    """
    ret = _validate(cfg, assume_yes=args.assume_yes, token=args.token)
    event.process_events()
    return ret


def _validate(cfg: config.EAConfig, assume_yes: bool, token=None) -> int:
    """Validate the cnonection from the machine to the API server,

    :param assume_yes: Assume a yes answer to any prompts requested.

    @return: 0 on success, 1 otherwise
    """

    try:
        actions.action_to_request(cfg, cmd="test", token=token)
    except exceptions.ConnectivityError as exc:
        LOG.exception(
            "Failed to access URL: %s", exc.url, exc_info=exc
        )
        msg = messages.E_CONNECTIVITY_ERROR.format(
            url=exc.url,
            cause_error=exc.cause_error,
        )
        event.error(error_msg=msg.msg, error_code=msg.name)
        event.info(info_msg=msg.msg, file_type=sys.stderr)
        sys.exit(1)

    event.info(messages.VALIDATE_SUCCESS)
    return 0


test_command = ProCommand(
    "test",
    help=messages.CLI_ROOT_TEST,
    description=messages.CLI_VALIDATE_DESC,
    action=action_validate,
    help_category=HelpCategory.OTHER,
    argument_groups=[
        ProArgumentGroup(
            arguments=[
                ProArgument(
                    "token", help=messages.CLI_ATTACH_TOKEN, nargs="?"
                ),
                ProArgument(
                    "--assume-yes",
                    help=messages.CLI_ASSUME_YES.format(command="test"),
                    action="store_true",
                ),
            ]
        )
    ],
)
