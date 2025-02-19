import argparse
import logging

from eaclient import (
    actions,
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
@cli_util.assert_lock_file("pro join")
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
        actions.attach_with_token(cfg, token=token)
    except exceptions.ConnectivityError:
        raise exceptions.AttachError()
    else:
        ret = 0
        '''do some post actions here.'''
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
