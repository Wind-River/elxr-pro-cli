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

import copy
import logging
import os
from functools import lru_cache
from typing import Any, Dict, Optional

from eaclient import (
    event_logger,
    system,
    util,
)

from eaclient.defaults import (
    BASE_CONTRACT_URL,
    CONFIG_DEFAULTS,
    CONFIG_FIELD_ENVVAR_ALLOWLIST,
    DEFAULT_CONFIG_FILE,
    DEFAULT_DATA_DIR,
)

from eaclient.files import user_config_file
from eaclient.yaml import safe_load

LOG = logging.getLogger(util.replace_top_level_logger_name(__name__))

# Keys visible and configurable using `pro config set|unset|show` subcommands
EA_CONFIGURABLE_KEYS = (
    "ea_apt_http_proxy",
    "ea_apt_https_proxy",
    "global_apt_http_proxy",
    "global_apt_https_proxy",
)

# Basic schema validation top-level keys for parse_config handling
VALID_EA_CONFIG_KEYS = (
    "contract_url",
    "data_dir",
    "log_file",
    "log_level",
)

event = event_logger.get_event_logger()


class EAConfig:
    ea_scoped_proxy_options = ("ea_apt_http_proxy", "ea_apt_https_proxy")
    global_scoped_proxy_options = (
        "global_apt_http_proxy",
        "global_apt_https_proxy",
    )

    def __init__(
        self,
        cfg: Optional[Dict[str, Any]] = None,
        user_config: Optional[user_config_file.UserConfigData] = None,
        series: Optional[str] = None,
    ) -> None:
        """"""
        if cfg:
            self.cfg_path = None
            self.cfg = cfg
            self.invalid_keys = None
        else:
            self.cfg_path = get_config_path()
            self.cfg, self.invalid_keys = parse_config(self.cfg_path)

        if user_config:
            self.user_config = user_config
        else:
            try:
                self.user_config = user_config_file.user_config.read()
            except Exception as e:
                LOG.warning("Error loading user config", exc_info=e)
                LOG.warning("Using default config values")
                self.user_config = user_config_file.UserConfigData()
        self.series = series

    @property
    def contract_url(self) -> str:
        return self.cfg.get("contract_url", BASE_CONTRACT_URL)

    @property
    def ea_apt_https_proxy(self) -> Optional[str]:
        return self.user_config.ea_apt_https_proxy

    @ea_apt_https_proxy.setter
    def ea_apt_https_proxy(self, value: str):
        self.user_config.ea_apt_https_proxy = value
        user_config_file.user_config.write(self.user_config)

    @property
    def ea_apt_http_proxy(self) -> Optional[str]:
        return self.user_config.ea_apt_http_proxy

    @ea_apt_http_proxy.setter
    def ea_apt_http_proxy(self, value: str):
        self.user_config.ea_apt_http_proxy = value
        user_config_file.user_config.write(self.user_config)

    @property  # type: ignore
    @lru_cache(maxsize=None)
    def global_apt_http_proxy(self) -> Optional[str]:
        global_val = self.user_config.global_apt_http_proxy
        if global_val:
            return global_val

        return None

    @global_apt_http_proxy.setter
    def global_apt_http_proxy(self, value: str):
        self.user_config.global_apt_http_proxy = value
        EAConfig.global_apt_http_proxy.fget.cache_clear()  # type: ignore
        user_config_file.user_config.write(self.user_config)

    @property  # type: ignore
    @lru_cache(maxsize=None)
    def global_apt_https_proxy(self) -> Optional[str]:
        global_val = self.user_config.global_apt_https_proxy
        if global_val:
            return global_val

        return None

    @global_apt_https_proxy.setter
    def global_apt_https_proxy(self, value: str):
        self.user_config.global_apt_https_proxy = value
        EAConfig.global_apt_https_proxy.fget.cache_clear()  # type: ignore
        user_config_file.user_config.write(self.user_config)

    @property
    def data_dir(self):
        return self.cfg.get("data_dir", DEFAULT_DATA_DIR)

    @property
    def log_level(self):
        log_level = self.cfg.get("log_level", "DEBUG")
        try:
            return getattr(logging, log_level.upper())
        except AttributeError:
            return logging.DEBUG

    @property
    def log_file(self) -> str:
        return self.cfg.get("log_file", CONFIG_DEFAULTS["log_file"])

    def warn_about_invalid_keys(self):
        if self.invalid_keys is not None:
            for invalid_key in sorted(self.invalid_keys):
                LOG.warning(
                    "Ignoring invalid eaclient.conf key: %s", invalid_key
                )


def get_config_path() -> str:
    """Get config path to be used when loading config dict."""
    config_file = os.environ.get("EA_CONFIG_FILE")
    if config_file:
        return config_file

    return DEFAULT_CONFIG_FILE


def parse_config(config_path=None):
    """Parse known Pro config file

    Attempt to find configuration in cwd and fallback to DEFAULT_CONFIG_FILE.
    Any missing configuration keys will be set to CONFIG_DEFAULTS.

    Values are overridden by any environment variable with prefix 'EA_'.

    @param config_path: Fullpath to pro configfile. If unspecified, use
        DEFAULT_CONFIG_FILE.

    @return: Dict of configuration values.
    """
    cfg = copy.copy(CONFIG_DEFAULTS)  # type: Dict[str, Any]

    if not config_path:
        config_path = get_config_path()

    LOG.debug("Using client configuration file at %s", config_path)
    if os.path.exists(config_path):
        cfg.update(safe_load(system.load_file(config_path)))
    env_keys = {}
    for key, value in os.environ.items():
        key = key.lower()
        if key.startswith("ea_"):
            # Strip leading EA_
            field_name = key[3:]
            if key in CONFIG_FIELD_ENVVAR_ALLOWLIST:
                env_keys[field_name] = value
    cfg.update(env_keys)
    if "data_dir" in cfg:
        cfg["data_dir"] = os.path.expanduser(cfg["data_dir"])

    invalid_keys = set(cfg.keys()).difference(VALID_EA_CONFIG_KEYS)
    for invalid_key in invalid_keys:
        cfg.pop(invalid_key)

    return cfg, invalid_keys
