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

from functools import wraps
from typing import Optional

from eaclient import (
    event_logger,
    exceptions,
    lock,
    util,
)

from eaclient.apt import AptProxyScope, setup_apt_proxy
from eaclient.config import EAConfig
from eaclient.files import machine_token

event = event_logger.get_event_logger()


def assert_lock_file(lock_holder=None):
    """Decorator asserting exclusive access to lock file"""

    def wrapper(f):
        @wraps(f)
        def new_f(*args, **kwargs):
            with lock.RetryLock(lock_holder=lock_holder, sleep_time=1):
                retval = f(*args, **kwargs)
            return retval

        return new_f

    return wrapper


def assert_root(f):
    """Decorator asserting root user"""

    @wraps(f)
    def new_f(*args, **kwargs):
        if not util.we_are_currently_root():
            raise exceptions.NonRootUserError()
        else:
            return f(*args, **kwargs)

    return new_f


def verify_json_format_args(f):
    """Decorator to verify if correct params are used for json format"""

    @wraps(f)
    def new_f(cmd_args, *args, **kwargs):
        if not cmd_args:
            return f(cmd_args, *args, **kwargs)

        if cmd_args.format == "json" and not cmd_args.assume_yes:
            raise exceptions.CLIJSONFormatRequireAssumeYes()
        else:
            return f(cmd_args, *args, **kwargs)

    return new_f


def assert_attached(raise_custom_error_function=None):
    """Decorator asserting attached config.
    :param msg_function: Optional function to generate a custom message
    if raising an UnattachedError
    """

    def wrapper(f):
        @wraps(f)
        def new_f(args, cfg, **kwargs):
            machine_token_file = machine_token.get_machine_token_file(cfg)
            is_attached = machine_token_file.is_attached
            if not is_attached:
                if raise_custom_error_function:
                    command = getattr(args, "command", "")
                    raise_custom_error_function(
                        command=command
                    )
                else:
                    raise exceptions.UnattachedError()
            return f(args, cfg=cfg, **kwargs)

        return new_f

    return wrapper


def assert_not_attached(f):
    """Decorator asserting unattached config."""

    @wraps(f)
    def new_f(args, cfg, **kwargs):
        machine_token_file = machine_token.get_machine_token_file(cfg)
        is_attached = machine_token_file.is_attached
        if is_attached:
            raise exceptions.AlreadyAttachedError(
                account_name = machine_token_file.contract_id
            )
        return f(args, cfg=cfg, **kwargs)
    return new_f


def configure_apt_proxy(
    cfg: EAConfig,
    scope: AptProxyScope,
    set_key: str,
    set_value: Optional[str],
) -> None:
    """
    Handles setting part the apt proxies - global and uaclient scoped proxies
    """
    if scope == AptProxyScope.GLOBAL:
        http_proxy = cfg.global_apt_http_proxy
        https_proxy = cfg.global_apt_https_proxy
    elif scope == AptProxyScope.EACLIENT:
        http_proxy = cfg.ea_apt_http_proxy
        https_proxy = cfg.ea_apt_https_proxy
    if "https" in set_key:
        https_proxy = set_value
    else:
        http_proxy = set_value
    setup_apt_proxy(
        http_proxy=http_proxy, https_proxy=https_proxy, proxy_scope=scope
    )
