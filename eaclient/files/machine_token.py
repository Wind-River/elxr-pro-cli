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
from typing import Any, Dict, Optional

from eaclient import defaults, exceptions, util
from eaclient.contract_data_types import PublicMachineTokenData
from eaclient.files.files import EAFile

_machine_token_file = None


class MachineTokenFile:
    def __init__(
        self,
        directory: str = defaults.DEFAULT_DATA_DIR,
    ):
        file_name = defaults.MACHINE_TOKEN_FILE
        self.private_file = EAFile(
            file_name, directory + "/" + defaults.PRIVATE_SUBDIR
        )
        self.public_file = EAFile(file_name, directory, False)
        self._machine_token = None  # type: Optional[Dict[str, Any]]
        self._entitlements = None
        self._contract_expiry_datetime = None

    def write(self, private_content: dict):
        """Update the machine_token file for both pub/private files"""
        if util.we_are_currently_root():
            private_content_str = json.dumps(
                private_content, cls=util.DatetimeAwareJSONEncoder
            )
            self.private_file.write(private_content_str)

            # PublicMachineTokenData only has public fields defined and
            # ignores all other (private) fields in from_dict
            public_content = PublicMachineTokenData.from_dict(
                private_content
            ).to_dict(keep_none=False)
            public_content_str = json.dumps(
                public_content, cls=util.DatetimeAwareJSONEncoder
            )
            self.public_file.write(public_content_str)

            self._machine_token = None
            self._entitlements = None
            self._contract_expiry_datetime = None
        else:
            raise exceptions.NonRootUserError()

    def delete(self):
        """Delete both pub and private files"""
        if util.we_are_currently_root():
            self.public_file.delete()
            self.private_file.delete()

            self._machine_token = None
            self._entitlements = None
            self._contract_expiry_datetime = None
        else:
            raise exceptions.NonRootUserError()

    def read(self) -> Optional[dict]:
        if util.we_are_currently_root():
            file_handler = self.private_file
        else:
            file_handler = self.public_file
        content = file_handler.read()
        if not content:
            return None
        try:
            content = json.loads(content, cls=util.DatetimeAwareJSONDecoder)
        except Exception:
            pass
        return content  # type: ignore

    @property
    def is_present(self):
        if util.we_are_currently_root():
            return self.public_file.is_present and self.private_file.is_present
        else:
            return self.public_file.is_present

    @property
    def machine_token(self):
        """Return the machine-token if cached in the machine token response."""
        if not self._machine_token:
            content = self.read()
            self._machine_token = content
        return self._machine_token

    def entitlements(self, series: Optional[str] = None):
        """Return configured entitlements keyed by entitlement named"""
        if self._entitlements:
            return self._entitlements
        if not self.machine_token:
            return {}
        self._entitlements = self.get_entitlements_from_token(
            self.machine_token, series
        )
        return self._entitlements

    @staticmethod
    def get_entitlements_from_token(
        machine_token: Dict[str, Any], series: Optional[str] = None
    ):
        """Return a dictionary of entitlements keyed by entitlement name.

        Return an empty dict if no entitlements are present.
        """
        if not machine_token:
            return {}

        entitlements = {}
        resources = machine_token.get("resources", [])
        if not resources:
            return {}

        ent_by_name = dict(
            (e.get("type"), e)
            for e in resources
        )
        for entitlement_name, ent_value in ent_by_name.items():
            entitlement_cfg = {"entitlement": ent_value}
            entitlements[entitlement_name] = entitlement_cfg
        return entitlements

    @property
    def is_attached(self):
        """Report whether this machine configuration is attached to EA."""
        return bool(self.machine_token)  # machine_token is removed on detach

    @property
    def contract_id(self):
        if self.machine_token:
            return self.machine_token.get("machineId", "")
        return None


def get_machine_token_file(cfg=None) -> MachineTokenFile:
    from eaclient.config import EAConfig

    global _machine_token_file

    if not _machine_token_file:
        if not cfg:
            cfg = EAConfig()
        _machine_token_file = MachineTokenFile(directory=cfg.data_dir)

    return _machine_token_file
