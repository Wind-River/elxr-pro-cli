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

from eaclient.files.machine_token import MachineTokenFile


class TestEntitlements:
    def test_entitlements_property_keyed_by_entitlement_name(self):
        """Return machine_token resourceEntitlements, keyed by name."""
        machine_token_file = MachineTokenFile()
        machine_token_file._machine_token = {
            "resources": [
                {
                    "type": "entitlement1",
                    "uri": "url1",
                    "login": "user",
                    "password": "passwd",
                    "suites": ["aria-pro-test"],
                    "components": ["main"],
                    "architectures": ["amd64", "arm64"],
                    "expires": "2025-03-21",
                },
            ],
            "machineId": "abcd",
            "token": "1234",
        }
        expected = {
            "entitlement1": {
                "entitlement": {
                    "type": "entitlement1",
                    "uri": "url1",
                    "login": "user",
                    "password": "passwd",
                    "suites": ["aria-pro-test",],
                    "components": ["main",],
                    "architectures": ["amd64", "arm64"],
                    "expires": "2025-03-21",
                },
            },
        }
        assert expected == machine_token_file.entitlements()
