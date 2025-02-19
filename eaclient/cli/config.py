from eaclient import (
    config,
    event_logger,
    exceptions,
    http,
    messages,
)

from eaclient.apt import AptProxyScope
from eaclient.cli import cli_util
from eaclient.cli.commands import ProArgument, ProArgumentGroup, ProCommand
from eaclient.cli.parser import HelpCategory

event = event_logger.get_event_logger()


def action_config(args, *, cfg, **kwargs):
    # Avoiding a circular import
    from eaclient.cli import get_parser

    get_parser().print_help_for_command("config")
    return 0


def action_config_show(args, *, cfg, **kwargs):
    """Perform the 'config show' action optionally limit output to a single key

    :return: 0 on success
    :raise eLxrProError: on invalid keys
    """
    if args.key:  # limit reporting config to a single config key
        if args.key not in config.EA_CONFIGURABLE_KEYS:
            raise exceptions.InvalidArgChoice(
                arg="'{}'".format(args.key),
                choices=", ".join(config.EA_CONFIGURABLE_KEYS),
            )
        print(
            "{key} {value}".format(
                key=args.key, value=getattr(cfg, args.key, None)
            )
        )
        return 0

    col_width = str(max([len(x) for x in config.EA_CONFIGURABLE_KEYS]) + 1)
    row_tmpl = "{key: <" + col_width + "} {value}"

    for key in config.EA_CONFIGURABLE_KEYS:
        print(row_tmpl.format(key=key, value=getattr(cfg, key, None)))

    if (cfg.global_apt_http_proxy or cfg.global_apt_https_proxy) and (
        cfg.ea_apt_http_proxy or cfg.ea_apt_https_proxy
    ):
        print(messages.CLI_CONFIG_GLOBAL_XOR_EA_PROXY)


@cli_util.assert_root
def action_config_set(args, *, cfg, **kwargs):
    """Perform the 'config set' action.

    @return: 0 on success, 1 otherwise
    """
    from eaclient.cli import get_parser

    parser = get_parser()
    try:
        set_key, set_value = args.key_value_pair.split("=")
    except ValueError:
        parser.print_help_for_command("config set")
        raise exceptions.GenericInvalidFormat(
            expected="<key>=<value>", actual=args.key_value_pair
        )
    if set_key not in config.EA_CONFIGURABLE_KEYS:
        parser.print_help_for_command("config set")
        raise exceptions.InvalidArgChoice(
            arg="<key>", choices=", ".join(config.EA_CONFIGURABLE_KEYS)
        )
    if not set_value.strip():
        parser.print_help_for_command("config set")
        raise exceptions.EmptyConfigValue(arg=set_key)

    if type(getattr(cfg, set_key, None)) == bool:
        if set_value.lower() not in ("true", "false"):
            raise exceptions.InvalidArgChoice(
                arg="<value>", choices="true, false"
            )
        set_value = set_value.lower() == "true"

    protocol_type = set_key.split("_")[2]
    if protocol_type == "http":
        validate_url = http.PROXY_VALIDATION_APT_HTTP_URL
    else:
        validate_url = http.PROXY_VALIDATION_APT_HTTPS_URL
    http.validate_proxy(protocol_type, set_value, validate_url)

    if set_key in cfg.ea_scoped_proxy_options:
        unset_current = bool(
            cfg.global_apt_http_proxy or cfg.global_apt_https_proxy
        )
        if unset_current:
            print(
                messages.WARNING_APT_PROXY_OVERWRITE.format(
                    current_proxy="pro scoped apt", previous_proxy="global apt"
                )
            )
        cli_util.configure_apt_proxy(
            cfg, AptProxyScope.EACLIENT, set_key, set_value
        )
        cfg.global_apt_http_proxy = None
        cfg.global_apt_https_proxy = None
    elif set_key in cfg.global_scoped_proxy_options:
        unset_current = bool(cfg.ea_apt_http_proxy or cfg.ea_apt_https_proxy)
        if unset_current:
            print(
                messages.WARNING_APT_PROXY_OVERWRITE.format(
                    current_proxy="global apt", previous_proxy="pro scoped apt"
                )
            )
        cli_util.configure_apt_proxy(
            cfg, AptProxyScope.GLOBAL, set_key, set_value
        )
        cfg.ea_apt_http_proxy = None
        cfg.ea_apt_https_proxy = None

    setattr(cfg, set_key, set_value)


@cli_util.assert_root
def action_config_unset(args, *, cfg, **kwargs):
    """Perform the 'config unset' action.

    @return: 0 on success, 1 otherwise
    """
    from eaclient.cli import get_parser

    if args.key not in config.EA_CONFIGURABLE_KEYS:
        parser = get_parser()
        parser.print_help_for_command("config unset")
        raise exceptions.InvalidArgChoice(
            arg="<key>", choices=", ".join(config.EA_CONFIGURABLE_KEYS)
        )
    if args.key in cfg.ea_scoped_proxy_options:
        cli_util.configure_apt_proxy(
            cfg, AptProxyScope.EACLIENT, args.key, None
        )
    elif args.key in cfg.global_scoped_proxy_options:
        cli_util.configure_apt_proxy(
            cfg, AptProxyScope.GLOBAL, args.key, None
        )

    setattr(cfg, args.key, None)
    return 0


show_subcommand = ProCommand(
    "show",
    help=messages.CLI_CONFIG_SHOW_DESC,
    description=messages.CLI_CONFIG_SHOW_DESC,
    action=action_config_show,
    argument_groups=[
        ProArgumentGroup(
            arguments=[
                ProArgument(
                    "key", help=messages.CLI_CONFIG_SHOW_KEY, nargs="?"
                )
            ]
        )
    ],
)

set_subcommand = ProCommand(
    "set",
    help=messages.CLI_CONFIG_SET_DESC,
    description=messages.CLI_CONFIG_SET_DESC,
    action=action_config_set,
    argument_groups=[
        ProArgumentGroup(
            arguments=[
                ProArgument(
                    "key_value_pair",
                    help=(
                        messages.CLI_CONFIG_SET_KEY_VALUE.format(
                            options=", ".join(config.EA_CONFIGURABLE_KEYS)
                        )
                    ),
                )
            ]
        )
    ],
)

unset_subcommand = ProCommand(
    "unset",
    help=messages.CLI_CONFIG_UNSET_DESC,
    description=messages.CLI_CONFIG_UNSET_DESC,
    action=action_config_unset,
    argument_groups=[
        ProArgumentGroup(
            arguments=[
                ProArgument(
                    "key",
                    help=(
                        messages.CLI_CONFIG_UNSET_KEY.format(
                            options=", ".join(config.EA_CONFIGURABLE_KEYS)
                        )
                    ),
                    metavar="key",
                )
            ]
        )
    ],
)

config_command = ProCommand(
    "config",
    help=messages.CLI_ROOT_CONFIG,
    description=messages.CLI_CONFIG_DESC,
    action=action_config,
    help_category=HelpCategory.OTHER,
    subcommands=[show_subcommand, set_subcommand, unset_subcommand],
)
