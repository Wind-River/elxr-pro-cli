import logging
import os
from typing import Optional
from urllib.parse import urlparse

from eaclient import defaults, event_logger, util
from eaclient.data_types import (
    DataObject,
    Field,
    StringDataValue,
)
from eaclient.files.data_types import DataObjectFile, DataObjectFileFormat
from eaclient.files.files import EAFile

# Config proxy fields that are visible and configurable
PROXY_FIELDS = [
    "global_apt_http_proxy",
    "global_apt_https_proxy",
    "ea_apt_http_proxy",
    "ea_apt_https_proxy",
    "http_proxy",
    "https_proxy",
]


class UserConfigData(DataObject):
    fields = [
        Field("global_apt_http_proxy", StringDataValue, required=False),
        Field("global_apt_https_proxy", StringDataValue, required=False),
        Field("ea_apt_http_proxy", StringDataValue, required=False),
        Field("ea_apt_https_proxy", StringDataValue, required=False),
        Field("http_proxy", StringDataValue, required=False),
        Field("https_proxy", StringDataValue, required=False),
    ]

    def __init__(
        self,
        global_apt_http_proxy: Optional[str] = None,
        global_apt_https_proxy: Optional[str] = None,
        ea_apt_http_proxy: Optional[str] = None,
        ea_apt_https_proxy: Optional[str] = None,
        http_proxy: Optional[str] = None,
        https_proxy: Optional[str] = None,
    ):
        self.global_apt_http_proxy = global_apt_http_proxy
        self.global_apt_https_proxy = global_apt_https_proxy
        self.ea_apt_http_proxy = ea_apt_http_proxy
        self.ea_apt_https_proxy = ea_apt_https_proxy
        self.http_proxy = http_proxy
        self.https_proxy = https_proxy


event = event_logger.get_event_logger()
LOG = logging.getLogger(util.replace_top_level_logger_name(__name__))


class UserConfigFileObject:
    def __init__(self, directory: str = defaults.DEFAULT_DATA_DIR):
        file_name = defaults.USER_CONFIG_FILE
        self._private = DataObjectFile(
            UserConfigData,
            EAFile(
                file_name,
                os.path.join(directory, defaults.PRIVATE_SUBDIR),
                private=True,
            ),
            DataObjectFileFormat.JSON,
            optional_type_errors_become_null=True,
        )
        self._public = DataObjectFile(
            UserConfigData,
            EAFile(file_name, directory, private=False),
            DataObjectFileFormat.JSON,
            optional_type_errors_become_null=True,
        )

    @property
    def public_config(self) -> UserConfigData:
        public_config = self._public.read()
        if public_config is None:
            public_config = UserConfigData()
        return public_config

    def redact_config_data(
        self, user_config: UserConfigData
    ) -> UserConfigData:
        redacted_data_dict = user_config.to_dict()
        for field in PROXY_FIELDS:
            value = redacted_data_dict.get(field)
            if value:
                parsed_url = urlparse(value)
                if parsed_url.username or parsed_url.password:
                    redacted_data_dict[field] = "<REDACTED>"
        return UserConfigData.from_dict(redacted_data_dict)

    def read(self) -> UserConfigData:
        if util.we_are_currently_root():
            private_config = self._private.read()
            if private_config is not None:
                return private_config
        public_config = self._public.read()
        if public_config is not None:
            return public_config
        return UserConfigData()

    def write(self, content: UserConfigData):
        self._private.write(content)
        redacted_content = self.redact_config_data(content)
        self._public.write(redacted_content)


user_config = UserConfigFileObject(defaults.DEFAULT_DATA_DIR)
