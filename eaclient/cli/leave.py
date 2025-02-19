from eaclient import (
    config,
    event_logger,
    messages,
    util,
)
from eaclient.cli import cli_util
from eaclient.cli.commands import ProArgument, ProArgumentGroup, ProCommand
from eaclient.cli.parser import HelpCategory
from eaclient.files import machine_token, state_files

event = event_logger.get_event_logger()


@cli_util.verify_json_format_args
@cli_util.assert_root
@cli_util.assert_attached()
@cli_util.assert_lock_file("pro leave")
def action_detach(args, *, cfg, **kwargs) -> int:
    """Perform the detach action for this machine.

    @return: 0 on success, 1 otherwise
    """
    ret = _detach(cfg, assume_yes=args.assume_yes)
    event.process_events()
    return ret


def _detach(cfg: config.EAConfig, assume_yes: bool) -> int:
    """Detach the machine from the active eLxr Pro subscription,

    :param cfg: a ``config.EAConfig`` instance
    :param assume_yes: Assume a yes answer to any prompts requested.
         In this case, it means automatically disable any service during
         detach.

    @return: 0 on success, 1 otherwise
    """

    if not util.prompt_for_confirmation(assume_yes=assume_yes):
        return 1

    machine_token_file = machine_token.get_machine_token_file(cfg)
    machine_token_file.delete()
    state_files.delete_state_files()
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
