from eaclient import (
    event_logger,
    messages,
)
from eaclient.cli.commands import ProArgument, ProArgumentGroup, ProCommand
from eaclient.cli.parser import HelpCategory


event = event_logger.get_event_logger()


def action_validate(args, **kwargs) -> int:
    """Perform the validation of connection to for this machine.

    @return: 0 on success, 1 otherwise
    """
    ret = _validate(assume_yes=args.assume_yes)
    event.process_events()
    return ret


def _validate(assume_yes: bool) -> int:
    """Validate the cnonection from the machine to the API server,

    :param assume_yes: Assume a yes answer to any prompts requested.

    @return: 0 on success, 1 otherwise
    """

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
                    "--assume-yes",
                    help=messages.CLI_ASSUME_YES.format(command="test"),
                    action="store_true",
                ),
            ]
        )
    ],
)
