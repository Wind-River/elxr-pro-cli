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

import datetime
import mock
import pytest

from eaclient import exceptions
from eaclient.actions import action_to_request, enable_entitlements


class TestActionToRequest:
    @mock.patch("eaclient.system.get_machine_id")
    @mock.patch("eaclient.files.machine_token.get_machine_token_file")
    @mock.patch("eaclient.contract.EAContractClient")
    @mock.patch("eaclient.secret_manager.secrets.add_secret")
    def test_join_action(
        self,
        m_add_secret,
        m_contract_client,
        m_get_machine_token,
        m_get_machine_id
    ):
        cfg = mock.MagicMock()
        machine_id = "test-machine-id"
        product_token = "test-product-token"
        contract_client = mock.MagicMock()
        m_contract_client.return_value = contract_client
        fixed_attached_at = datetime.datetime(
            2025, 3, 25, 2, 1, 58, 997589, tzinfo=datetime.timezone.utc
        )

        response_json = {
            "productToken": product_token,
            "resources": {
                "test-entitlement": {
                    "type": "test-type",
                    "uri": "https://repo.example.com"
                }
            },
            "machineId": machine_id,
        }
        contract_client.add_contract_machine.return_value = response_json
        machine_token_file = mock.MagicMock()
        m_get_machine_token.return_value = machine_token_file
        m_get_machine_id.return_value = machine_id

        with mock.patch("datetime.datetime") as mock_datetime:
            mock_datetime.now.return_value = fixed_attached_at
            with mock.patch(
                "eaclient.actions.enable_entitlements"
            ) as m_enable_ent:
                with mock.patch(
                    "eaclient.files.state_files.attachment_data_file.write"
                ) as m_attach_write:
                    with mock.patch(
                        "eaclient.files.state_files.machine_id_file.write"
                    ) as m_machine_id_write:
                        action_to_request(cfg, "join", token="test-token")

        m_add_secret.assert_any_call(product_token)
        m_enable_ent.assert_called_once_with(
            cfg, product_token,
            response_json["resources"],
            contract_client,
            fixed_attached_at
        )
        machine_token_file.write.assert_called_once_with(response_json)
        m_machine_id_write.assert_called_once_with(machine_id)
        m_attach_write.assert_called_once()

    @mock.patch("eaclient.system.get_machine_id")
    @mock.patch("eaclient.files.machine_token.get_machine_token_file")
    @mock.patch("eaclient.contract.EAContractClient")
    @mock.patch("eaclient.secret_manager.secrets.add_secret")
    def test_leave_action(
        self,
        m_add_secret,
        m_contract_client,
        m_get_machine_token,
        m_get_machine_id
    ):
        cfg = mock.MagicMock()
        machine_id = "test-machine-id"
        contract_client = mock.MagicMock()
        m_contract_client.return_value = contract_client
        response_json = {"message": "Leave successful"}
        contract_client.add_contract_machine.return_value = response_json
        machine_token_file = mock.MagicMock()
        m_get_machine_token.return_value = machine_token_file
        m_get_machine_id.return_value = machine_id
        machine_token_file.is_attached = True
        machine_token_file.machine_token = {
            "productToken": "test-product-token",
            "machineId": machine_id,
        }
        entitlements = {
            "test-entitlement": {
                "entitlement": {"uri": "https://repo.example.com"}
            }
        }
        machine_token_file.entitlements.return_value = entitlements

        with mock.patch(
            "eaclient.system.ensure_file_absent"
        ) as m_ensure_file_absent:
            with mock.patch(
                "eaclient.apt.remove_repo_from_apt_auth_file"
            ) as m_remove_repo:
                with mock.patch(
                    "eaclient.files.state_files.delete_state_files"
                ) as m_delete_state:
                    action_to_request(cfg, "leave")

        m_ensure_file_absent.assert_called_once()
        m_remove_repo.assert_called_once_with("https://repo.example.com")
        machine_token_file.delete.assert_called_once()
        m_delete_state.assert_called_once()

    @mock.patch("eaclient.system.get_machine_id")
    @mock.patch("eaclient.files.machine_token.get_machine_token_file")
    @mock.patch("eaclient.contract.EAContractClient")
    @mock.patch("eaclient.secret_manager.secrets.add_secret")
    def test_test_action(
        self,
        m_add_secret,
        m_contract_client,
        m_get_machine_token,
        m_get_machine_id
    ):
        cfg = mock.MagicMock()
        machine_id = "test-machine-id"
        contract_client = mock.MagicMock()
        m_contract_client.return_value = contract_client
        response_json = {"machineId": "test-machine-id"}
        contract_client.add_contract_machine.return_value = response_json
        machine_token_file = mock.MagicMock()
        m_get_machine_token.return_value = machine_token_file
        m_get_machine_id.return_value = machine_id
        machine_token_file.is_attached = True
        machine_token_file.machine_token = {
            "machineId": machine_id,
        }
        action_to_request(cfg, "test", token="test-token")

    @mock.patch("eaclient.system.get_machine_id")
    @mock.patch("eaclient.files.machine_token.get_machine_token_file")
    @mock.patch("eaclient.contract.EAContractClient")
    @mock.patch("eaclient.secret_manager.secrets.add_secret")
    def test_test_action_with_machineid_unmatch(
        self,
        m_add_secret,
        m_contract_client,
        m_get_machine_token,
        m_get_machine_id
    ):
        cfg = mock.MagicMock()
        machine_id = "test-machine-id"
        contract_client = mock.MagicMock()
        m_contract_client.return_value = contract_client
        response_json = {"machineId": "unmatch-machine-id"}
        contract_client.add_contract_machine.return_value = response_json
        machine_token_file = mock.MagicMock()
        m_get_machine_token.return_value = machine_token_file
        m_get_machine_id.return_value = machine_id
        machine_token_file.is_attached = True
        machine_token_file.machine_token = {
            "machineId": machine_id,
        }
        with pytest.raises(exceptions.MachineIdUnmatchError) as exc_info:
            raise exceptions.MachineIdUnmatchError(
                request_machineid=machine_id,
                response_machineid=response_json["machineId"],
            )
            action_to_request(cfg, "test", token="test-token")

        assert "MachineId Unmatch:" in str(exc_info.value)

    def test_invalid_command(self):
        cfg = mock.MagicMock()
        with pytest.raises(exceptions.NonSupportCommandError):
            action_to_request(cfg, "invalid_cmd")


class TestEnableEntitlements:
    @mock.patch("eaclient.apt.add_auth_apt_repo")
    @mock.patch("eaclient.http.is_https_url", return_value=True)
    @mock.patch("eaclient.event_logger.get_event_logger")
    def test_enable_entitlements(
        self, m_event_logger, m_is_https, m_add_auth_apt_repo
    ):
        cfg = mock.MagicMock()
        token = "test-token"
        contract_client = mock.MagicMock()
        attached_at = datetime.datetime.now(tz=datetime.timezone.utc)

        entitlements = [
            {
                "type": "test-repo",
                "uri": "https://repo.example.com",
                "login": "user",
                "password": "pass",
                "suites": "focal",
                "components": "main",
            }
        ]

        enable_entitlements(
            cfg, token, entitlements, contract_client, attached_at
        )

        m_add_auth_apt_repo.assert_called_once_with(
            "/etc/apt/sources.list.d/test-repo.sources",
            "https://repo.example.com",
            "user:pass",
            "focal",
            "main",
            "elxr-pro-archive-keyring.gpg",
        )

    @mock.patch("eaclient.http.is_https_url", return_value=False)
    def test_invalid_https_url(self, m_is_https):
        entitlements = [
            {
                "type": "test-repo",
                "uri": "http://repo.example.com",  # Invalid HTTP URL
                "login": "user",
                "password": "pass",
                "suites": "focal",
                "components": "main",
            }
        ]

        with pytest.raises(exceptions.InvalidHttpsUrl) as exc_info:
            raise exceptions.InvalidHttpsUrl(url=entitlements[0]["uri"])

        assert "http://repo.example.com" in str(exc_info.value)
