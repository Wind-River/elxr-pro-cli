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

import logging
import os
import shutil

from eaclient import exceptions, util

LOG = logging.getLogger(util.replace_top_level_logger_name(__name__))


def export_gpg_key(source_keyfile: str, destination_keyfile: str) -> None:
    """Copy a specific key from source_keyring_dir into destination_keyfile

    :param source_keyfile: Path of source keyring file to export.
    :param destination_keyfile: The filename created with the single exported
        key.

    :raise ELxrProError: Any GPG errors or if specific key does not exist in
        the source_keyring_file.
    """
    LOG.debug("Exporting GPG key %s", source_keyfile)
    if not os.path.exists(source_keyfile):
        raise exceptions.GPGKeyNotFound(keyfile=source_keyfile)
    shutil.copy(source_keyfile, destination_keyfile)
    os.chmod(destination_keyfile, 0o644)
