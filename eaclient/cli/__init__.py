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

"""Client to manage eLxr Pro services on a machine."""

import logging
import sys

from eaclient import (
    event_logger,
    exceptions,
    defaults,
    log,
    messages,
    system,
    util,
    version
)

from eaclient.cli.config import config_command
from eaclient.cli.help import help_command
from eaclient.cli.join import join_command
from eaclient.cli.leave import leave_command
from eaclient.cli.parser import HelpCategory, ProArgumentParser
from eaclient.cli.validate import test_command
from eaclient.config import EAConfig
from eaclient.log import get_user_or_root_log_file_path

event = event_logger.get_event_logger()
LOG = logging.getLogger(util.replace_top_level_logger_name(__name__))

NAME = "elxr-pro"

COMMANDS = [
    join_command,
    config_command,
    leave_command,
    test_command,
    help_command,
]


def get_parser():
    parser = ProArgumentParser(
        prog=NAME,
        use_main_help=False,
        epilog=messages.CLI_HELP_EPILOG.format(name=NAME, command="<command>"),
    )
    parser.add_help_entry(
        HelpCategory.FLAGS,
        "-h, --help",
        messages.CLI_HELP_FLAG_DESC.format(name=NAME),
    )

    parser.add_argument(
        "--debug", action="store_true", help=messages.CLI_ROOT_DEBUG
    )
    parser.add_help_entry(
        HelpCategory.FLAGS, "--debug", messages.CLI_ROOT_DEBUG
    )

    parser.add_argument(
        "--version",
        action="version",
        version=version.get_version(),
        help=messages.CLI_ROOT_VERSION.format(name=NAME),
    )
    parser.add_help_entry(
        HelpCategory.FLAGS,
        "--version",
        messages.CLI_ROOT_VERSION.format(name=NAME),
    )

    subparsers = parser.add_subparsers(
        title=messages.CLI_AVAILABLE_COMMANDS,
        dest="command",
        metavar="<command>",
    )
    subparsers.required = True

    for command in COMMANDS:
        command.register(subparsers)

    return parser


def warn_about_non_elxr_distro():
    distro = system.get_release_info().distribution
    if distro != "eLxr":
        event.info(messages.NON_ELXR_DISTRO.format(distro=distro))
        sys.exit(1)


def set_event_mode(cmd_args):
    """Set the right event mode based on the args provided"""
    if cmd_args.command in ("join", "leave", "test"):
        event.set_command(cmd_args.command)
        if hasattr(cmd_args, "format"):
            if cmd_args.format == "json":
                event.set_event_mode(event_logger.EventLoggerMode.JSON)
            if cmd_args.format == "yaml":
                event.set_event_mode(event_logger.EventLoggerMode.YAML)


def main_error_handler(func):
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except KeyboardInterrupt:
            LOG.error("KeyboardInterrupt")
            sys.exit(1)
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

            event.process_events()
            sys.exit(1)
        except exceptions.ELxrProError as exc:
            LOG.error(exc.msg)
            event.error(
                error_msg=exc.msg,
                error_code=exc.msg_code,
                additional_info=exc.additional_info,
            )
            event.info(info_msg="{}".format(exc.msg), file_type=sys.stderr)

            event.process_events()
            sys.exit(exc.exit_code)
        except Exception as e:
            LOG.exception("Unhandled exception, please file a bug")
            event.info(
                info_msg=messages.UNEXPECTED_ERROR.format(
                    error_msg=str(e),
                    log_path=get_user_or_root_log_file_path(),
                ).msg,
                file_type=sys.stderr,
            )
            event.error(
                error_msg=getattr(e, "msg", str(e)), error_type="exception"
            )

            event.process_events()
            sys.exit(1)

    return wrapper


@main_error_handler
def main(sys_argv=None):
    log.setup_cli_logging(
        defaults.CONFIG_DEFAULTS["log_level"],
        defaults.CONFIG_DEFAULTS["log_file"],
    )

    cfg = EAConfig()
    log.setup_cli_logging(cfg.log_level, cfg.log_file)

    if not sys_argv:
        sys_argv = sys.argv

    parser = get_parser()
    cli_arguments = sys_argv[1:]
    if not cli_arguments:
        parser.print_help()
        sys.exit(0)

    # Version is --version
    if cli_arguments[0] == "version":
        cli_arguments[0] = "--version"

    # Grab everything after a "--" if present and handle separately
    if "--" in cli_arguments:
        double_dash_index = cli_arguments.index("--")
        pro_cli_args = cli_arguments[:double_dash_index]
        extra_args = cli_arguments[double_dash_index + 1 :]
    else:
        pro_cli_args = cli_arguments
        extra_args = []

    args = parser.parse_args(args=pro_cli_args)
    if args.debug:
        console_handler = logging.StreamHandler(sys.stderr)
        console_handler.setLevel(logging.DEBUG)
        logging.getLogger("elxr-pro").addHandler(console_handler)

    set_event_mode(args)

    LOG.debug("Executed with sys.argv: %r" % sys_argv)

    warn_about_non_elxr_distro()

    cfg.warn_about_invalid_keys()

    pro_environment = [
        "{}={}".format(k, v)
        for k, v in sorted(util.get_pro_environment().items())
    ]
    if pro_environment:
        LOG.debug("Executed with environment variables: %r" % pro_environment)

    return_value = args.action(args, cfg=cfg, extra_args=extra_args)

    return return_value


if __name__ == "__main__":
    sys.exit(main())
