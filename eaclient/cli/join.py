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
import logging
import sys

from eaclient import (
    actions,
    defaults,
    event_logger,
    exceptions,
    messages,
    secret_manager,
    util,
)
from eaclient.cli import cli_util
from eaclient.cli.commands import ProArgument, ProArgumentGroup, ProCommand
from eaclient.cli.parser import HelpCategory
from eaclient.data_types import AttachActionsConfigFile, IncorrectTypeError
from eaclient.yaml import safe_load

event = event_logger.get_event_logger()
LOG = logging.getLogger(util.replace_top_level_logger_name(__name__))


@cli_util.assert_not_attached
@cli_util.assert_root
@cli_util.assert_lock_file("elxr-pro join")
def action_attach(args, *, cfg, **kwargs):
    if args.token and args.attach_config:
        raise exceptions.CLIAttachTokenArgXORConfig()
    elif not args.token and not args.attach_config:
        raise exceptions.CLIAttachTokenArgORConfigRequired()
    elif args.token:
        token = args.token
        secret_manager.secrets.add_secret(token)
    else:
        try:
            attach_config = AttachActionsConfigFile.from_dict(
                safe_load(args.attach_config)
            )
        except IncorrectTypeError as e:
            raise exceptions.AttachInvalidConfigFileError(
                config_name=args.attach_config.name, error=e.msg
            )

        token = attach_config.token

    try:
        actions.action_to_request(
            cfg, cmd="join", token=token, pro_only_enable=args.pro_only
        )
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
    else:
        ret = 0
        '''do some post actions here.'''
        event.process_events()
        event.info(
            messages.PROMPT_MOTD_JOIN.format(
                homepage_url=defaults.HOMEPAGE_URL
            )
        )
        return ret


join_command = ProCommand(
    "join",
    help=messages.CLI_ROOT_ATTACH,
    description=messages.CLI_ATTACH_DESC,
    action=action_attach,
    preserve_description=True,
    help_category=HelpCategory.QUICKSTART,
    help_position=2,
    argument_groups=[
        ProArgumentGroup(
            arguments=[
                ProArgument(
                    "token", help=messages.CLI_ATTACH_TOKEN, nargs="?"
                ),
                ProArgument(
                    "--attach-config",
                    help=messages.CLI_ATTACH_ATTACH_CONFIG,
                    type=argparse.FileType("r"),
                ),
                ProArgument(
                    "--pro-only",
                    help=messages.CLI_PRO_ONLY,
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
