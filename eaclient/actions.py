from eaclient import config


def attach_with_token(
    cfg: config.EAConfig,
    token: str,
    silent: bool = False,
) -> None:
    """
    Common functionality to take a token and attach via contract backend
    :raise ConnectivityError: On unexpected connectivity issues to contract
        server or inability to access identity doc from metadata service.
    :raise ContractAPIError: On unexpected errors when talking to the contract
        server.
    """
