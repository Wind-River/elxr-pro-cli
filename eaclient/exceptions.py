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

from typing import Optional

from eaclient import messages


class ProcessExecutionError(IOError):
    def __init__(
        self,
        cmd: str,
        exit_code: Optional[int] = None,
        stdout: str = "",
        stderr: str = "",
    ) -> None:
        self.stdout = stdout
        self.stderr = stderr
        self.exit_code = exit_code
        if not exit_code:
            message = messages.SUBP_INVALID_COMMAND.format(cmd=cmd)
        else:
            message = messages.SUBP_COMMAND_FAILED.format(
                cmd=cmd, exit_code=exit_code, stderr=stderr
            )
        super().__init__(message)


class ELxrProError(Exception):
    """
    Base class for all of our custom errors.
    All possible exceptions from our API should extend this class.
    """

    _msg = None  # type: messages.NamedMessage
    _formatted_msg = None  # type: messages.FormattedNamedMessage

    exit_code = 1

    def __init__(self, **kwargs) -> None:
        if self._formatted_msg is not None:
            self.named_msg = self._formatted_msg.format(
                **kwargs
            )  # type: messages.NamedMessage
        else:
            self.named_msg = self._msg

        self.additional_info = kwargs

        for key, value in kwargs.items():
            setattr(self, key, value)

    @property
    def msg(self):
        return self.named_msg.msg

    @property
    def msg_code(self):
        return self.named_msg.name

    def __str__(self):
        return self.named_msg.msg


###############################################################################
#                              APT                                            #
###############################################################################


class APTProcessConflictError(ELxrProError):
    _msg = messages.E_APT_PROCESS_CONFLICT


class APTInvalidRepoError(ELxrProError):
    _formatted_msg = messages.E_APT_UPDATE_INVALID_URL_CONFIG


class APTUpdateProcessConflictError(ELxrProError):
    _msg = messages.E_APT_UPDATE_PROCESS_CONFLICT


class APTUpdateInvalidRepoError(ELxrProError):
    _formatted_msg = messages.E_APT_UPDATE_INVALID_REPO


class APTUpdateFailed(ELxrProError):
    _formatted_msg = messages.E_APT_UPDATE_FAILED


class APTInstallProcessConflictError(ELxrProError):
    _msg = messages.E_APT_INSTALL_PROCESS_CONFLICT


class APTInstallInvalidRepoError(ELxrProError):
    _formatted_msg = messages.E_APT_INSTALL_INVALID_REPO


class APTInvalidCredentials(ELxrProError):
    _formatted_msg = messages.E_APT_INVALID_CREDENTIALS


class APTTimeout(ELxrProError):
    _formatted_msg = messages.E_APT_TIMEOUT


class APTUnexpectedError(ELxrProError):
    _formatted_msg = messages.E_APT_UNEXPECTED_ERROR


class APTCommandTimeout(ELxrProError):
    _formatted_msg = messages.E_APT_COMMAND_TIMEOUT


###############################################################################
#                              PROXY/NETWORK                                  #
###############################################################################


class MachineIdUnmatchError(ELxrProError):
    _formatted_msg = messages.E_MACHINEID_UNMATCH


class InvalidHttpsUrl(ELxrProError):
    _formatted_msg = messages.E_INVALID_HTTPS_URL


class InvalidUrl(ELxrProError):
    _formatted_msg = messages.E_INVALID_URL


class ProxyNotWorkingError(ELxrProError):
    _formatted_msg = messages.E_NOT_SETTING_PROXY_NOT_WORKING


class ProxyInvalidUrl(ELxrProError):
    _formatted_msg = messages.E_NOT_SETTING_PROXY_INVALID_URL


class PycurlRequiredError(ELxrProError):
    _msg = messages.E_PYCURL_REQUIRED


class PycurlError(ELxrProError):
    _formatted_msg = messages.E_PYCURL_ERROR


class ProxyAuthenticationFailed(ELxrProError):
    _msg = messages.E_PROXY_AUTH_FAIL


class ExternalAPIError(ELxrProError):
    _formatted_msg = messages.E_EXTERNAL_API_ERROR
    code = None  # type: int
    url = None  # type: str
    body = None  # type: str

    def __str__(self):
        return "{}: [{}], {}".format(self.code, self.url, self.body)


class ContractAPIError(ExternalAPIError):
    pass


class PycurlCACertificatesError(ELxrProError):
    _msg = messages.E_PYCURL_CA_CERTIFICATES

    def __init__(self, url, **kwargs) -> None:
        super().__init__(**kwargs)
        self.url = url


class ConnectivityError(ELxrProError, IOError):
    _formatted_msg = messages.E_CONNECTIVITY_ERROR

    def __init__(
        self,
        cause: Exception,
        url: str,
    ):
        if getattr(cause, "reason", None):
            cause_error = str(getattr(cause, "reason"))
        else:
            cause_error = str(cause)
        IOError.__init__(self, cause_error)
        ELxrProError.__init__(self, cause_error=cause_error, url=url)

        # Even though we already set those variable through ELxrProError
        # we need to set them again to avoid mypy warnings
        self.cause_error = cause_error
        self.url = url

###############################################################################
#                              JOIN                                           #
###############################################################################


class AlreadyAttachedError(ELxrProError):
    """An exception to be raised when a command needs an unattached system."""

    exit_code = 2
    _formatted_msg = messages.E_ALREADY_ATTACHED


class AttachError(ELxrProError):
    """An exception to be raised when we detect a generic attach error."""

    exit_code = 1
    _msg = messages.E_ATTACH_FAILURE


class AttachInvalidConfigFileError(ELxrProError):
    _formatted_msg = messages.E_ATTACH_CONFIG_READ_ERROR


class AttachInvalidTokenError(ELxrProError):
    _msg = messages.E_ATTACH_INVALID_TOKEN


class AttachForbiddenExpired(ELxrProError):
    _formatted_msg = messages.E_ATTACH_FORBIDDEN_EXPIRED


class AttachForbiddenNotYet(ELxrProError):
    _formatted_msg = messages.E_ATTACH_FORBIDDEN_NOT_YET


class AttachForbiddenNever(ELxrProError):
    _formatted_msg = messages.E_ATTACH_FORBIDDEN_NEVER


class AttachExpiredToken(ELxrProError):
    _msg = messages.E_ATTACH_EXPIRED_TOKEN


class EmptyTokenError(ELxrProError):
    _msg = messages.E_EMPTY_TOKEN


class UnattachedError(ELxrProError):
    """An exception to be raised when a machine needs to be attached."""

    _msg = messages.E_UNATTACHED


###############################################################################
#                              CLI                                            #
###############################################################################


class InvalidArgChoice(ELxrProError):
    _formatted_msg = messages.E_CLI_VALID_CHOICES


class EmptyConfigValue(ELxrProError):
    _formatted_msg = messages.E_CLI_EMPTY_CONFIG_VALUE


class GenericInvalidFormat(ELxrProError):
    _formatted_msg = messages.E_CLI_EXPECTED_FORMAT


class CLIJSONFormatRequireAssumeYes(ELxrProError):
    _msg = messages.E_JSON_FORMAT_REQUIRE_ASSUME_YES


class CLIAttachTokenArgXORConfig(ELxrProError):
    _msg = messages.E_ATTACH_TOKEN_ARG_XOR_CONFIG


class CLIAttachTokenArgORConfigRequired(ELxrProError):
    _msg = messages.E_ATTACH_TOKEN_ARG_OR_CONFIG_REQUIRED


###############################################################################
#                               MISCELLANEOUS                                 #
###############################################################################


class LockHeldError(ELxrProError):
    """An exception for when another pro operation is in progress

    :param lock_request: String of the command requesting the lock
    :param lock_holder: String of the command that currently holds the lock
    :param pid: Integer of the process id of the lock_holder
    """

    _formatted_msg = messages.E_LOCK_HELD_ERROR
    pid = None  # type: int


class GPGKeyNotFound(ELxrProError):
    _formatted_msg = messages.E_GPG_KEY_NOT_FOUND


class NonRootUserError(ELxrProError):
    """An exception to be raised when a user needs to be root."""

    _msg = messages.E_NONROOT_USER


class NonSupportCommandError(ELxrProError):
    """An exception to be raised when a command isn't supported."""

    msg = messages.E_NONSUPPORT_CMD


class UnknownProcessorType(ELxrProError):
    _formatted_msg = messages.E_UNKNOWN_PROCESSOR_TYPE


class ArchNotSupported(ELxrProError):
    _formatted_msg = messages.E_ARCH_NOT_SUPPORTED


class VariantUnexpectedError(ELxrProError):
    _formatted_msg = messages.E_VARIANT_UNEXPECTED_ERROR


###############################################################################
#                              FILES/FORMATS                                  #
###############################################################################


class InvalidFileFormatError(ELxrProError):
    _formatted_msg = messages.E_INVALID_FILE_FORMAT


class InvalidLockFile(ELxrProError):
    _formatted_msg = messages.E_INVALID_LOCK_FILE
