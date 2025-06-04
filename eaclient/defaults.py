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

"""
Project-wide default settings

These are in their own file so they can be imported by setup.py before we have
any of our dependencies installed.
"""

import os

# Base directories
EAC_ETC_PATH = "/etc/elxr-advantage"
EAC_RUN_PATH = "/run/elxr-advantage"
DEFAULT_DATA_DIR = "/var/lib/elxr-pro"
DEFAULT_LOG_DIR = "/var/log"


# Relative paths
MACHINE_TOKEN_FILE = "machine-token.json"
CONFIG_FILE = "eaclient.conf"
USER_CONFIG_FILE = "user-config.json"
DEFAULT_LOG_FILE_BASE_NAME = "elxr-advantage"
PRIVATE_SUBDIR = "private"
MESSAGES_SUBDIR = "messages"
INTERFACE_FILES_SUBDIR = "interfaces"
USER_CACHE_SUBDIR = "elxr-pro"
PRIVATE_ELXR_CACHE_SUBDIR = "apt-esm"

DEFAULT_PRIVATE_MACHINE_TOKEN_PATH = os.path.join(
    DEFAULT_DATA_DIR, PRIVATE_SUBDIR, MACHINE_TOKEN_FILE
)
DEFAULT_PRIVATE_DATA_DIR = os.path.join(DEFAULT_DATA_DIR, PRIVATE_SUBDIR)
MESSAGES_DIR = os.path.join(DEFAULT_DATA_DIR, MESSAGES_SUBDIR)
INTERFACE_FILES_DIR = os.path.join(DEFAULT_DATA_DIR, INTERFACE_FILES_SUBDIR)
DEFAULT_CONFIG_FILE = os.path.join(EAC_ETC_PATH, CONFIG_FILE)
DEFAULT_LOG_PREFIX = os.path.join(DEFAULT_LOG_DIR, DEFAULT_LOG_FILE_BASE_NAME)
ESM_APT_ROOTDIR = os.path.join(DEFAULT_DATA_DIR, PRIVATE_ELXR_CACHE_SUBDIR)

HOMEPAGE_URL = "https://elxr.pro/"
BASE_CONTRACT_URL = "https://api.elxr.pro"

PRINT_WRAP_WIDTH = 80
CONTRACT_EXPIRY_GRACE_PERIOD_DAYS = 14
CONTRACT_EXPIRY_PENDING_DAYS = 20
ATTACH_FAIL_DATE_FORMAT = "%B %d, %Y"

CONFIG_DEFAULTS = {
    "contract_url": BASE_CONTRACT_URL,
    "data_dir": DEFAULT_DATA_DIR,
    "log_level": "debug",
    "log_file": "{}.log".format(DEFAULT_LOG_PREFIX),
}

CONFIG_FIELD_ENVVAR_ALLOWLIST = [
    "ea_data_dir",
    "ea_log_file",
    "ea_log_level",
]

ROOT_READABLE_MODE = 0o600
WORLD_READABLE_MODE = 0o644

SSL_CERTS_PATH = "/etc/ssl/certs/ca-certificates.crt"
