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
