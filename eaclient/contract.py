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
import socket
from typing import Optional

import eaclient.files.machine_token as mtf
from eaclient import (
    event_logger,
    exceptions,
    system,
    util,
    version,
)

from eaclient.config import EAConfig
from eaclient.http import serviceclient
from eaclient.system import cpu_type

# Here we describe every endpoint from the elxr-pro contracts
# service that is used by this client implementation.
API_V1_JOIN_CONTRACT_MACHINE = "/api/v1/actions/join"
API_V1_LEAVE_CONTRACT_MACHINE = "/api/v1/actions/leave"
API_V1_TEST_CONTRACT_MACHINE = "/api/v1/actions/test"

event = event_logger.get_event_logger()
LOG = logging.getLogger(util.replace_top_level_logger_name(__name__))


class EAContractClient(serviceclient.EAServiceClient):
    cfg_url_base_attr = "contract_url"

    def __init__(
        self,
        cfg: Optional[EAConfig] = None,
    ) -> None:
        super().__init__(cfg=cfg)
        self.machine_token_file = mtf.get_machine_token_file()

    @util.retry(socket.timeout, retry_sleeps=[1, 2, 2])
    def add_contract_machine(
        self, cmd, attachment_dt, contract_token=None, machine_id=None
    ):
        """Requests machine attach to the provided machine_id.

        @param contract_token: Token string providing authentication to
            ContractBearer service endpoint.
        @param machine_id: Optional unique system machine id. When absent,
            contents of /etc/machine-id will be used.

        @return: Dict of the JSON response containing the machine-token.
        """
        if not machine_id:
            machine_id = system.get_machine_id(self.cfg)

        headers = self.headers()
        headers.update({"Authorization": "Bearer {}".format(contract_token)})
        machine_info = self._get_machine_info()
        data = {
            "machineId": machine_id,
            "machineInfo": machine_info,
        }

        test_without_token = False
        if cmd == 'join':
            req_url = API_V1_JOIN_CONTRACT_MACHINE
        elif cmd == 'leave':
            req_url = API_V1_LEAVE_CONTRACT_MACHINE
        elif cmd == 'test':
            req_url = API_V1_TEST_CONTRACT_MACHINE
            if not contract_token:
                test_without_token = True
        else:
            raise exceptions.NonSupportCommandError()

        if contract_token:
            data["productToken"] = contract_token

        response = self.request_url(
            req_url, data=data, headers=headers
        )

        if response.code != 200:
            if response.code == 401 and test_without_token:
                pass
            else:
                raise exceptions.ContractAPIError(
                    url=req_url,
                    code=response.code,
                    body=response.body,
                )

        response_json = response.json_dict
        return response_json

    def _get_machine_info(self):
        """Return a dict of machine info data for contract requests"""

        machine_info = {
            "distribution": system.get_release_info().distribution,
            "kernel": system.get_kernel_info().uname_release,
            "series": system.get_release_info().series,
            "architecture": system.get_dpkg_arch(),
            "desktop": "true",
            "virt": system.get_virt_type(),
            "clientVersion": version.get_version(),
            "cpu_type": cpu_type.get_cpu_type(),
        }
        return machine_info
