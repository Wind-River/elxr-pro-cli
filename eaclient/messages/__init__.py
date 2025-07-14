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

import sys
from gettext import NullTranslations, translation
from typing import Dict, Optional

from eaclient.messages import urls

if sys.stdout.encoding is None or "UTF-8" not in sys.stdout.encoding.upper():
    t = NullTranslations()
else:
    t = translation("elxr-pro", "/usr/share/locale", fallback=True)


###############################################################################
#                              MISCELLANEOUS                                  #
###############################################################################
# Things that don't fit with the others. Some of these are used as pieces in
# messages below.
# If one of the groups of messages in this section grows enough, it should get
# its own section.


class TxtColor:
    OKGREEN = "\033[92m"
    DISABLEGREY = "\033[37m"
    INFOBLUE = "\033[94m"
    WARNINGYELLOW = "\033[93m"
    FAIL = "\033[91m"
    BOLD = "\033[1m"
    ENDC = "\033[0m"


STANDALONE_YES = t.gettext("yes")
STANDALONE_NO = t.gettext("no")

OKGREEN_CHECK = TxtColor.OKGREEN + "✔" + TxtColor.ENDC
FAIL_X = TxtColor.FAIL + "✘" + TxtColor.ENDC
BLUE_INFO = TxtColor.INFOBLUE + "[info]" + TxtColor.ENDC
GREEN_INFO = TxtColor.OKGREEN + "[info]" + TxtColor.ENDC
YELLOW_WARN = TxtColor.WARNINGYELLOW + "[warn]" + TxtColor.ENDC

PROMPT_YES_NO = t.gettext("""Are you sure? (y/N) """)
PROCEED_YES_NO = t.gettext("Do you want to proceed? (y/N) ")

CLI_INTERRUPT_RECEIVED = t.gettext("Interrupt received; exiting.")

LOCK_HELD = t.gettext("""Operation in progress: {lock_holder} (pid:{pid})""")

REFRESH_CONTRACT_SUCCESS = t.gettext(
    "Successfully refreshed your subscription."
)
REFRESH_CONFIG_SUCCESS = t.gettext(
    "Successfully processed your eLxr Pro configuration."
)
REFRESH_MESSAGES_SUCCESS = t.gettext(
    "Successfully updated eLxr Pro related APT and MOTD messages."
)


MISSING_YAML_MODULE = t.gettext(
    """\
Couldn't import the YAML module.
Make sure the 'python3-yaml' package is installed correctly
and /usr/lib/python3/dist-packages is in your PYTHONPATH."""
)
BROKEN_YAML_MODULE = t.gettext(
    "Error while trying to parse a yaml file using 'yaml' from {path}"
)

PROMPT_MOTD_JOIN = (
    "\n"
    + GREEN_INFO
    + t.gettext(
        """\
 motd from server
For more information about your eLxr Pro subscription,
go to {homepage_url}
"""
    )
)

NON_ELXR_DISTRO = (
    "\n"
    + YELLOW_WARN
    + t.gettext(
        """\
Only eLxr OS is supported, distro {distro} is NOT available.
"""
    )
)


###############################################################################
#                      GENERIC SYSTEM OPERATIONS                              #
###############################################################################


EXECUTING_COMMAND = t.gettext("Executing `{command}`")
EXECUTING_COMMAND_FAILED = t.gettext("Executing `{command}` failed.")
SUBP_INVALID_COMMAND = t.gettext("Invalid command specified '{cmd}'.")
SUBP_COMMAND_FAILED = t.gettext(
    "Failed running command '{cmd}' [exit({exit_code})]." " Message: {stderr}"
)

APT_POLICY_FAILED = t.gettext("Failure checking APT policy.")
APT_UPDATING_LISTS = t.gettext("Updating package lists")
APT_UPDATING_LIST = t.gettext("Updating {name} package lists")
APT_UPDATE_FAILED = t.gettext("APT update failed.")
APT_INSTALL_FAILED = t.gettext("APT install failed.")

APT_ADD_AUTH_FILE_SUCCESS = t.gettext("Establishing authentication file.")
APT_ADD_REPOSITORY_SOURCE_SUCCESS = t.gettext(
    "Enabling eLxr Pro Package Repository sources."
)


###############################################################################
#                         CONFIGURATION                                       #
###############################################################################


SETTING_SERVICE_PROXY_SCOPE = t.gettext("Setting {scope} APT proxy")


CLI_CONFIG_GLOBAL_XOR_EA_PROXY = t.gettext(
    "\nError: Setting global apt proxy and pro scoped apt proxy at the"
    " same time is unsupported. No apt proxy is set."
)


WARNING_APT_PROXY_OVERWRITE = t.gettext(
    """\
Warning: Setting the {current_proxy} proxy will overwrite the {previous_proxy}
proxy previously set via `elxr-pro config`.
"""
)


###############################################################################
#                        JOIN/LEAVE/TEST SUBCOMMAND                           #
###############################################################################


DETACH_SUCCESS = (
    "\n"
    + BLUE_INFO
    + t.gettext(" This machine is now detached.")
)

FORCE_DETACH_PROMPT = (
    "\n"
    + BLUE_INFO
    + t.gettext(
        " Force to leave, only remove local elxr-pro data."
        " You can try join again and leave to detach machine."
    )
)


CLI_MAGIC_ATTACH_INIT = t.gettext("Initiating join operation...")

VALIDATE_SUCCESS = t.gettext("Connection to API server successful.")


###############################################################################
#                        CLI HELP TEXT                                        #
###############################################################################
# This encompasses help text for subcommands, flags, and arguments for the CLI
# Also, any generic strings about the CLI itself go here.


CLI_HELP_EPILOG = t.gettext(
    "Use {name} {command} --help for more information about a command."
)

CLI_HELP_FLAG_DESC = t.gettext(
    "Displays help on {name} and command line options"
)
CLI_DETACH_DESC = t.gettext(
    "Detach this machine from an eLxr Pro subscription."
)
CLI_HELP_DESC = t.gettext(
    "Provide detailed information about eLxr Pro services."
)
CLI_VALIDATE_DESC = t.gettext(
    "Validate the connection to the API server."
)

CLI_ROOT_DEBUG = t.gettext("show all debug log messages to console")
CLI_ROOT_VERSION = t.gettext("show version of {name}")
CLI_ROOT_ATTACH = t.gettext(
    "attach this machine to an eLxr Pro subscription"
)
CLI_ROOT_CONFIG = t.gettext("manage eLxr Pro configuration on this machine")
CLI_ROOT_DETACH = t.gettext(
    "remove this machine from an eLxr Pro subscription"
)
CLI_ROOT_TEST = t.gettext("validate the connection to the API server")
CLI_ROOT_HELP = t.gettext(
    "show detailed information about eLxr Pro services"
)

CLI_CONFIG_SHOW_DESC = t.gettext("Show customizable configuration settings")
CLI_CONFIG_SHOW_KEY = t.gettext(
    "Optional key or key(s) to show configuration settings."
)
CLI_CONFIG_SET_DESC = t.gettext(
    "Set and apply eLxr Pro configuration settings"
)
CLI_CONFIG_SET_KEY_VALUE = t.gettext(
    "key=value pair to configure for eLxr Pro services."
    " Key must be one of: {options}"
)
CLI_CONFIG_UNSET_DESC = t.gettext("Unset eLxr Pro configuration setting")
CLI_CONFIG_UNSET_KEY = t.gettext(
    "configuration key to unset from eLxr Pro services. One of: {options}"
)
CLI_CONFIG_DESC = t.gettext("Manage eLxr Pro configuration")


CLI_HELP_HEADER_QUICK_START = t.gettext("Quick start commands")
CLI_HELP_HEADER_OTHER = t.gettext("Other commands")


CLI_FLAGS = t.gettext("Flags")
CLI_AVAILABLE_COMMANDS = t.gettext("Available Commands")
CLI_FORMAT_DESC = t.gettext(
    "output in the specified format (default: {default}), "
    "but json format must require --assume-yes flag."
)
CLI_ASSUME_YES = t.gettext(
    "do not prompt for confirmation before performing the {command}"
)


CLI_ATTACH_DESC = t.gettext(
    """\
Join this machine to an eLxr Pro subscription with a token obtained from:
{url}

When running this command without a token, it will generate a short code
and prompt you to attach the machine to your eLxr Pro account using a web
browser.
The "attach-config" option can be used to provide a file with the token
and optionally.

The exit code will be:

    * 0: on successful attach
    * 1: in case of any error while trying to attach
    * 2: if the machine is already attached"""
).format(url=urls.PRO_DASHBOARD)

CLI_ATTACH_TOKEN = t.gettext("token obtained for eLxr Pro authentication")
CLI_ATTACH_ATTACH_CONFIG = t.gettext(
    "use the provided attach config file instead of passing the token on"
    "the cli, and the format should be like 'token: abcdefg123456789'"
)
CLI_PRO_ONLY = t.gettext(
    "drop the original apt repo sources(elxr|debian), just access pro only."
)


CLI_FORCE_TO_LEAVE = t.gettext(
    "force to leave from an eLxr Pro subscription.(Just remove local data)"
)


###############################################################################
#                              NAMED MESSAGES                                 #
###############################################################################
# These are mostly used in json output of cli commands for errors or warnings


class NamedMessage:
    def __init__(
        self,
        name: str,
        msg: str,
        additional_info: Optional[Dict[str, str]] = None,
    ):
        self.name = name
        self.msg = msg
        # we should use this field whenever we want to provide
        # extra information to the message. This is specially
        # useful if the message represents an error.
        self.additional_info = additional_info

    def __eq__(self, other):
        return (
            self.msg == other.msg
            and self.name == other.name
            and self.additional_info == other.additional_info
        )

    def __repr__(self):
        return "NamedMessage({}, {}, {})".format(
            self.name.__repr__(),
            self.msg.__repr__(),
            self.additional_info.__repr__(),
        )


class FormattedNamedMessage:
    def __init__(self, name: str, msg: str):
        self.name = name
        self.tmpl_msg = msg

    def format(self, **msg_params) -> NamedMessage:
        return NamedMessage(
            name=self.name, msg=self.tmpl_msg.format(**msg_params)
        )

    def __repr__(self):
        return "FormattedNamedMessage({}, {})".format(
            self.name.__repr__(),
            self.tmpl_msg.__repr__(),
        )


###############################################################################
#                              ERROR MESSAGES                                 #
###############################################################################


E_APT_PROCESS_CONFLICT = NamedMessage(
    "apt-process-conflict", t.gettext("Another process is running APT.")
)

E_APT_UPDATE_INVALID_URL_CONFIG = FormattedNamedMessage(
    "apt-update-invalid-url-config",
    t.gettext(
        """\
APT update failed to read APT config for the following:
{failed_repos}"""
    ),
)

E_APT_UPDATE_PROCESS_CONFLICT = NamedMessage(
    "apt-update-failed-process-conflict",
    APT_UPDATE_FAILED + " " + E_APT_PROCESS_CONFLICT.msg,
)

E_APT_UPDATE_INVALID_REPO = FormattedNamedMessage(
    "apt-update-invalid-repo", APT_UPDATE_FAILED + "\n{repo_msg}"
)

E_APT_UPDATE_FAILED = FormattedNamedMessage(
    "apt-update-failed", APT_UPDATE_FAILED + "\n{detail}"
)

E_APT_INSTALL_PROCESS_CONFLICT = NamedMessage(
    "apt-install-failed-process-conflict",
    APT_INSTALL_FAILED + " " + E_APT_PROCESS_CONFLICT.msg,
)

E_APT_INSTALL_INVALID_REPO = FormattedNamedMessage(
    "apt-install-invalid-repo", APT_INSTALL_FAILED + " {repo_msg}"
)


E_APT_INVALID_CREDENTIALS = FormattedNamedMessage(
    "apt-invalid-credentials",
    t.gettext("Invalid APT credentials provided for {repo}"),
)

E_APT_TIMEOUT = FormattedNamedMessage(
    "apt-timeout",
    t.gettext("Timeout trying to access APT repository at {repo}"),
)

E_APT_UNEXPECTED_ERROR = FormattedNamedMessage(
    "apt-unexpected-error",
    t.gettext(
        """\
Unexpected APT error.
{detail}
See /var/log/elxr-advantage.log"""
    ),
)

E_APT_COMMAND_TIMEOUT = FormattedNamedMessage(
    "apt-command-timeout",
    t.gettext(
        "Cannot validate credentials for APT repo."
        " Timeout after {seconds} seconds trying to reach {repo}."
    ),
)

E_NOT_SETTING_PROXY_NOT_WORKING = FormattedNamedMessage(
    "proxy-not-working",
    t.gettext('"{proxy}" is not working. Not setting as proxy.'),
)

E_NOT_SETTING_PROXY_INVALID_URL = FormattedNamedMessage(
    "proxy-invalid-url",
    t.gettext('"{proxy}" is not a valid url. Not setting as proxy.'),
)

E_PYCURL_REQUIRED = NamedMessage(
    "pycurl-required",
    t.gettext(
        "To use an HTTPS proxy for HTTPS connections, please install "
        "pycurl with `apt install python3-pycurl`"
    ),
)

E_PYCURL_ERROR = FormattedNamedMessage(
    "pycurl-error", t.gettext("PycURL Error: {e}")
)

E_PROXY_AUTH_FAIL = NamedMessage(
    "proxy-auth-fail", t.gettext("Proxy authentication failed")
)

E_CONNECTIVITY_ERROR = FormattedNamedMessage(
    "connectivity-error",
    t.gettext(
        """\
Failed to connect to {url}
{cause_error}
"""
    ),
)

E_EXTERNAL_API_ERROR = FormattedNamedMessage(
    "external-api-error", t.gettext("Error connecting to {url}: {code} {body}")
)

E_ALREADY_ATTACHED = FormattedNamedMessage(
    name="already-attached",
    msg=t.gettext(
        "This machine is already attached to '{account_name}'\n"
        "To use a different subscription first run: sudo elxr-pro leave."
    ),
)

E_ATTACH_FAILURE = NamedMessage(
    "attach-failure",
    t.gettext("Failed to attach machine. See {url}").format(
        url=urls.PRO_DASHBOARD
    ),
)

E_ATTACH_CONFIG_READ_ERROR = FormattedNamedMessage(
    "attach-config-read-error",
    t.gettext("Error while reading {config_name}:\n{error}"),
)

E_ATTACH_INVALID_TOKEN = NamedMessage(
    "attach-invalid-token",
    t.gettext("Invalid token. See {url}").format(url=urls.PRO_DASHBOARD),
)

E_EMPTY_TOKEN = NamedMessage(
    "token-empty",
    t.gettext("Empty token. See {url}").format(url=urls.PRO_DASHBOARD),
)

E_TOKEN_FORBIDDEN_EXPIRED = FormattedNamedMessage(
    "token-forbidden-expired",
    t.gettext(
        """\
Expired token.
Visit {url} to manage contract tokens."""
    ).format(url=urls.PRO_DASHBOARD),
)

E_TOKEN_FORBIDDEN_NOT_YET = FormattedNamedMessage(
    "token-forbidden-not-yet",
    t.gettext(
        """\
Contract "{{contract_id}}" is not effective until {{date}}
Visit {url} to manage contract tokens."""
    ).format(url=urls.PRO_DASHBOARD),
)

E_ATTACH_FORBIDDEN_EXPIRED = FormattedNamedMessage(
    "attach-forbidden-expired",
    t.gettext("Attach denied:\n") + E_TOKEN_FORBIDDEN_EXPIRED.tmpl_msg,
)


E_ATTACH_FORBIDDEN_NOT_YET = FormattedNamedMessage(
    "attach-forbidden-not-yet",
    t.gettext("Attach denied:\n") + E_TOKEN_FORBIDDEN_NOT_YET.tmpl_msg,
)

E_ATTACH_FORBIDDEN_NEVER = FormattedNamedMessage(
    "attach-forbidden-never",
    t.gettext(
        """\
Attach denied:
Contract "{{contract_id}}" has never been effective
Visit {url} to manage contract tokens."""
    ).format(url=urls.PRO_DASHBOARD),
)

E_ATTACH_EXPIRED_TOKEN = NamedMessage(
    "attach-experied-token",
    t.gettext(
        """\
Expired token or contract. To obtain a new token visit: {url}"""
    ).format(url=urls.PRO_DASHBOARD),
)

E_UNATTACHED = NamedMessage(
    "unattached",
    "\n"
    + YELLOW_WARN
    + t.gettext(
        """\
 This machine is not attached to an eLxr Pro subscription.
See {url}"""
    ).format(url=urls.PRO_HOME_PAGE),
)


E_CLI_VALID_CHOICES = FormattedNamedMessage(
    "invalid-arg-choice", "\n" + t.gettext("{arg} must be one of: {choices}")
)

E_CLI_EMPTY_CONFIG_VALUE = FormattedNamedMessage(
    "empty-value",
    t.gettext("Empty value provided for {arg}."),
)

E_CLI_EXPECTED_FORMAT = FormattedNamedMessage(
    "generic-invalid-format",
    "\n" + t.gettext("Expected {expected} but found: {actual}"),
)

E_LOCK_HELD_ERROR = FormattedNamedMessage(
    "lock-held-error",
    t.gettext(
        """\
Unable to perform: {lock_request}.
"""
    )
    + LOCK_HELD,
)

E_GPG_KEY_NOT_FOUND = FormattedNamedMessage(
    "gpg-key-not-found", t.gettext("GPG key '{keyfile}' not found.")
)

E_NONROOT_USER = NamedMessage(
    "nonroot-user",
    t.gettext("This command must be run as root (try using sudo)."),
)

E_NONSUPPORT_CMD = NamedMessage(
    "nonsupport-cmd",
    t.gettext("This request command is not supportted."),
)

E_INVALID_FILE_FORMAT = FormattedNamedMessage(
    name="invalid-file-format",
    msg=t.gettext("{file_name} is not valid {file_format}"),
)

E_INVALID_LOCK_FILE = FormattedNamedMessage(
    "invalid-lock-file",
    t.gettext(
        """\
There is a corrupted lock file in the system. To continue, please remove it
from the system by running:

$ sudo rm {lock_file_path}"""
    ),
)

E_JSON_FORMAT_REQUIRE_ASSUME_YES = NamedMessage(
    "json-format-require-assume-yes",
    t.gettext(
        """\
json formatted response requires --assume-yes flag."""
    ),
)

E_ATTACH_TOKEN_ARG_XOR_CONFIG = NamedMessage(
    "attach-token-xor-config",
    t.gettext(
        """\
Do not pass the TOKEN arg if you are using --attach-config.
Include the token in the attach-config file instead.
    """
    ),
)

E_ATTACH_TOKEN_ARG_OR_CONFIG_REQUIRED = NamedMessage(
    "attach-token-or-config-required",
    "\n"
    + YELLOW_WARN
    + t.gettext(
        """\
 Pass the TOKEN arg or use --attach-config.
Include the token in the attach-config file.
    """
    ),
)

E_INCORRECT_TYPE_ERROR_MESSAGE = FormattedNamedMessage(
    "incorrect-type",
    t.gettext(
        "Expected value with type {expected_type} but got type: {got_type}"
    ),
)

E_INCORRECT_LIST_ELEMENT_TYPE_ERROR_MESSAGE = FormattedNamedMessage(
    "incorrect-list-element-type",
    t.gettext("Got value with incorrect type at index {index}:\n{nested_msg}"),
)

E_INCORRECT_FIELD_TYPE_ERROR_MESSAGE = FormattedNamedMessage(
    "incorrect-field-type",
    t.gettext(
        'Got value with incorrect type for field "{key}":\n{nested_msg}'
    ),
)

E_INCORRECT_ENUM_VALUE_ERROR_MESSAGE = FormattedNamedMessage(
    "incorrect-enum-value",
    t.gettext(
        "Value provided was not found in {enum_class}'s allowed: "
        "value: {values}"
    ),
)

E_PYCURL_CA_CERTIFICATES = NamedMessage(
    "pycurl-ca-certificates-error", "Problem reading SSL CA certificates"
)

E_INVALID_HTTPS_URL = FormattedNamedMessage(
    "invalid-https-url",
    t.gettext("Invalid Https URL: {url}")
)

E_INVALID_URL = FormattedNamedMessage(
    "invalid-url",
    t.gettext("Invalid URL: {url}"),
)

E_MACHINEID_UNMATCH = FormattedNamedMessage(
    "machineid unmatch",
    t.gettext(
        "MachineId Unmatch: {request_machineid} and {response_machineid}"
    ),
)

UNEXPECTED_ERROR = FormattedNamedMessage(
    "unexpected-error",
    t.gettext(
        """\
An unexpected error occurred: {error_msg}
For more details, see the log: {log_path}"""
    ),
)

E_UNKNOWN_PROCESSOR_TYPE = FormattedNamedMessage(
    "unknown-processor-type",
    t.gettext("Unknown processor type: {processor_type}"),
)

E_ARCH_NOT_SUPPORTED = FormattedNamedMessage(
    "arch-not-supported",
    t.gettext("{arch} is not supported for {variant}"),
)

E_VARIANT_UNEXPECTED_ERROR = FormattedNamedMessage(
    "variant-unexpected",
    t.gettext("{variant} is unexpected, just 'server' and 'edge' are valid"),
)

E_VERIFICATION_ERROR_ISSUER_CERTIFICATES = FormattedNamedMessage(
    "ssl-verification-error-ca-issuer-certificate",
    t.gettext(
        """\
Failed to access URL: {url}
Please check local issuer CA or request help from your IT department."""
    ),
)

E_VERIFICATION_ERROR_CA_NOT_VALID = FormattedNamedMessage(
    "ssl-verification-error-ca-is-not-valid",
    t.gettext(
        """\
Failed to access URL: {url}
Certificate is not yet valid, please calibrate the local target time."""
    ),
)

E_TRY_AGAIN_PROMPT = FormattedNamedMessage(
    "try-again-later",
    t.gettext(" Please try again later, or contract your system vendor.")
)

E_RESOURCE_NOT_FOUND = FormattedNamedMessage(
    "resource-not-found",
    t.gettext("Resource Not Found.") + E_TRY_AGAIN_PROMPT.tmpl_msg,
)

E_INTERNAL_SERVER_ERROR = FormattedNamedMessage(
    "internal-server-error",
    t.gettext("Internal server error.") + E_TRY_AGAIN_PROMPT.tmpl_msg,
)

E_SERVICE_UNAVAILABLE = FormattedNamedMessage(
    "service-unavailable",
    t.gettext("Service unavailable.") + E_TRY_AGAIN_PROMPT.tmpl_msg,
)
