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

import json
import logging
import os
from typing import Any, Dict, Optional

from eaclient import defaults, event_logger, exceptions, system, util

event = event_logger.get_event_logger()
LOG = logging.getLogger(util.replace_top_level_logger_name(__name__))


class EAFile:
    def __init__(
        self,
        name: str,
        directory: str = defaults.DEFAULT_DATA_DIR,
        private: bool = True,
    ):
        self._directory = directory
        self._file_name = name
        self._is_private = private
        self._path = os.path.join(self._directory, self._file_name)

    @property
    def path(self) -> str:
        return self._path

    @property
    def is_private(self) -> bool:
        return self._is_private

    @property
    def is_present(self):
        return os.path.exists(self.path)

    def write(self, content: str):
        file_mode = (
            defaults.ROOT_READABLE_MODE
            if self.is_private
            else defaults.WORLD_READABLE_MODE
        )
        # try/except-ing here avoids race conditions the best
        try:
            if os.path.basename(self._directory) == defaults.PRIVATE_SUBDIR:
                os.makedirs(self._directory, mode=0o700)
            else:
                os.makedirs(self._directory)
        except OSError:
            pass

        system.write_file(self.path, content, file_mode)

    def read(self) -> Optional[str]:
        content = None
        try:
            content = system.load_file(self.path)
        except FileNotFoundError:
            LOG.debug("Tried to load %s but file does not exist", self.path)
        return content

    def delete(self):
        system.ensure_file_absent(self.path)


class ProJSONFile:
    def __init__(
        self,
        pro_file: EAFile,
    ):
        self.pro_file = pro_file

    def write(self, content: Dict[str, Any]):
        self.pro_file.write(
            content=json.dumps(content, cls=util.DatetimeAwareJSONEncoder)
        )

    def read(self) -> Optional[Dict[str, Any]]:
        content = self.pro_file.read()

        if content:
            try:
                return json.loads(content, cls=util.DatetimeAwareJSONDecoder)
            except json.JSONDecodeError as e:
                raise exceptions.InvalidJson(
                    source=self.pro_file.path, out="\n" + str(e)
                )

        return None

    def delete(self):
        return self.pro_file.delete()

    @property
    def is_present(self):
        return self.pro_file.is_present


class UserCacheFile(EAFile):
    def __init__(self, name: str):
        super().__init__(
            name, directory=system.get_user_cache_dir(), private=False
        )
