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

from typing import List, Optional

from eaclient.data_types import (
    DataObject,
    Field,
    StringDataValue,
    data_list,
)


class Resource(DataObject):
    fields = [
        Field("type", StringDataValue, False),
        Field("uri", StringDataValue, False),
        Field("login", StringDataValue, False),
        Field("password", StringDataValue, False),
        Field("suites", data_list(StringDataValue), False),
        Field("components", data_list(StringDataValue), False),
        Field("architectures", data_list(StringDataValue), False),
        Field("expires", StringDataValue, False),
    ]

    def _init__(
        self,
        type: Optional[str],
        uri: Optional[str],
        login: Optional[str],
        password: Optional[str],
        suites: Optional[List[str]],
        components: Optional[List[str]],
        architectures: Optional[List[str]],
        expires: Optional[str],
    ):
        self.type = type
        self.uri = uri
        self.login = login
        self.password = password
        self.suites = suites
        self.components = components
        self.architectures = architectures
        self.expires = expires


class PublicMachineTokenData(DataObject):
    fields = [
        Field("resources", data_list(Resource), False),
        Field("machineId", StringDataValue, False),
        Field("productToken", StringDataValue, False),
        Field("message", StringDataValue, False),
    ]

    def __init__(
        self,
        resources: Optional[List[Resource]],
        machineId: Optional[str],
        productToken: Optional[str],
        message: Optional[str],
    ):
        self.resources = resources
        self.machineId = machineId
        self.productToken = productToken
        self.message = message
