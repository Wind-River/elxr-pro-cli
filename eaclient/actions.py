import datetime
import logging
from typing import List

from eaclient import (
    apt,
    config,
    contract,
    event_logger,
    exceptions,
    messages,
    secret_manager,
    system,
    util,
)

from eaclient.files import machine_token, state_files

from eaclient.files.state_files import (
    AttachmentData,
    attachment_data_file,
    machine_id_file,
)

event = event_logger.get_event_logger()
LOG = logging.getLogger(util.replace_top_level_logger_name(__name__))


def action_to_request(
    cfg: config.EAConfig,
    cmd: str,
    token: str = None,
    silent: bool = False,
) -> None:
    """
    Common functionality to take a token and attach via contract backend
    :raise ConnectivityError: On unexpected connectivity issues to contract
        server or inability to access identity doc from metadata service.
    :raise ContractAPIError: On unexpected errors when talking to the contract
        server.
    """
    machine_id = system.get_machine_id(cfg)
    machine_token_file = machine_token.get_machine_token_file(cfg)
    if cmd == 'leave':
        if machine_token_file.is_attached:
            token = machine_token_file.machine_token.get("productToken")
            machine_id = machine_token_file.machine_token.get("machineId")
        else:
            raise exceptions.UnattachedError()

    secret_manager.secrets.add_secret(token)
    contract_client = contract.EAContractClient(cfg)
    attached_at = datetime.datetime.now(tz=datetime.timezone.utc)

    response_json = contract_client.add_contract_machine(
        cmd=cmd,
        attachment_dt=attached_at,
        contract_token=token,
        machine_id=machine_id
    )
    product_token = response_json.get("productToken", "")
    secret_manager.secrets.add_secret(product_token)

    if cmd == 'join':
        entitlements = response_json.get("resources", {})
        enable_entitlements(
            cfg,
            product_token,
            entitlements,
            contract_client,
            attached_at,
        )

        machine_token_file.write(response_json)

        machine_id = response_json.get(
            "machineId", system.get_machine_id(cfg)
        )
        system.get_machine_id.cache_clear()
        machine_id_file.write(machine_id)
        attachment_data_file.write(AttachmentData(attached_at=attached_at))
    elif cmd == 'leave':
        resp_msg = response_json.get("message")
        if resp_msg == "Leave successful":
            repo_file_tmpl = "/etc/apt/sources.list.d/{name}.sources"
            entitlements = machine_token_file.entitlements()
            for entitlement_name, ent_value in entitlements.items():
                repo_url = ent_value.get("entitlement").get("uri")
                repo_file = repo_file_tmpl.format(name=entitlement_name)
                system.ensure_file_absent(repo_file)
                apt.remove_repo_from_apt_auth_file(repo_url)

            machine_token_file.delete()
            state_files.delete_state_files()
    elif cmd == 'test':
        if token:
            resp_machineid = response_json.get("machineId", "")
            if resp_machineid != machine_id:
                raise exceptions.MachineIdUnmatchError(
                    reqeust_machineid=machine_id,
                    response_machineid=resp_machineid,
                )
    else:
        raise exceptions.NonSupportCommandError()


def enable_entitlements(
    cfg: config.EAConfig,
    token: str,
    entitlements: List[str],
    contract_client: contract.EAContractClient,
    attached_at: datetime.datetime,
):
    repo_file_tmpl = "/etc/apt/sources.list.d/{name}.sources"
    repo_key_file = "elxr-pro-archive-keyring.gpg"

    event.info(messages.APT_ADD_AUTH_FILE_SUCCESS)
    for ent in entitlements:
        entitlement_name = ent.get("type")
        repo_url = ent.get("uri")
        login = ent.get("login")
        password = ent.get("password")
        id_token = login + ":" + password
        repo_suites = ent.get("suites")
        components = ent.get("components")

        apt.add_auth_apt_repo(
            repo_file_tmpl.format(name=entitlement_name),
            repo_url,
            id_token,
            repo_suites,
            components,
            repo_key_file
        )

    event.info(messages.APT_ADD_REPOSITORY_SOURCE_SUCCESS)
