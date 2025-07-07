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
from eaclient.cli import cli_util
from eaclient.cli.commands import ProArgument, ProArgumentGroup, ProCommand
from eaclient.cli.parser import HelpCategory

event = event_logger.get_event_logger()
LOG = logging.getLogger(util.replace_top_level_logger_name(__name__))


@cli_util.verify_json_format_args
@cli_util.assert_root
@cli_util.assert_attached()
@cli_util.assert_lock_file("pro leave")
def action_detach(args, *, cfg, **kwargs) -> int:
    """Perform the detach action for this machine.

    @return: 0 on success, 1 otherwise
    """
    ret = _detach(cfg, assume_yes=args.assume_yes, force=args.force)
    event.process_events()
    return ret


def _detach(cfg: config.EAConfig, assume_yes: bool, force: False) -> int:
    """Detach the machine from the active eLxr Pro subscription,

    :param cfg: a ``config.EAConfig`` instance
    :param assume_yes: Assume a yes answer to any prompts requested.
         In this case, it means automatically disable any service during
         detach.

    @return: 0 on success, 1 otherwise
    """

    if not util.prompt_for_confirmation(assume_yes=assume_yes):
        return 1

    try:
        actions.action_to_request(cfg, cmd="leave", force=force)
    except exceptions.ConnectivityError as exc:
        if "CERTIFICATE_VERIFY_FAILED" in str(exc):
            if "unable to get local issuer certificate" in str(exc):
                tmpl = messages.E_VERIFICATION_ERROR_ISSUER_CERTIFICATES
            elif "certificate is not yet valid" in str(exc):
                tmpl = messages.E_VERIFICATION_ERROR_CA_NOT_VALID
            msg = tmpl.format(url=exc.url)
        else:
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

    if force:
        event.info(messages.FORCE_DETACH_PROMPT)
    else:
        event.info(messages.DETACH_SUCCESS)
    return 0


leave_command = ProCommand(
    "leave",
    help=messages.CLI_ROOT_DETACH,
    description=messages.CLI_DETACH_DESC,
    action=action_detach,
    help_category=HelpCategory.OTHER,
    argument_groups=[
        ProArgumentGroup(
            arguments=[
                ProArgument(
                    "--assume-yes",
                    help=messages.CLI_ASSUME_YES.format(command="leave"),
                    action="store_true",
                ),
                ProArgument(
                    "--force",
                    help=messages.CLI_FORCE_TO_LEAVE,
                    action="store_true",
                ),
                ProArgument(
                    "--format",
                    help=messages.CLI_FORMAT_DESC.format(default="cli"),
                    action="store",
                    choices=["cli", "json"],
                    default="cli",
                ),
            ]
        )
    ],
)
