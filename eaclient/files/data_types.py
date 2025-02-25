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
from enum import Enum
from typing import Callable, Dict, Generic, Optional, Type, TypeVar

from eaclient import exceptions
from eaclient.data_types import DataObject
from eaclient.files.files import EAFile
from eaclient.util import DatetimeAwareJSONDecoder
from eaclient.yaml import parser as yaml_parser
from eaclient.yaml import safe_dump, safe_load


class DataObjectFileFormat(Enum):
    JSON = "json"
    YAML = "yaml"


DOFType = TypeVar("DOFType", bound=DataObject)


class DataObjectFile(Generic[DOFType]):
    def __init__(
        self,
        data_object_cls: Type[DOFType],
        ea_file: EAFile,
        file_format: DataObjectFileFormat = DataObjectFileFormat.JSON,
        preprocess_data: Optional[Callable[[Dict], Dict]] = None,
        optional_type_errors_become_null: bool = False,
    ):
        self.data_object_cls = data_object_cls
        self.ea_file = ea_file
        self.file_format = file_format
        self.preprocess_data = preprocess_data
        self.optional_type_errors_become_null = (
            optional_type_errors_become_null
        )

    def read(self) -> Optional[DOFType]:
        raw_data = self.ea_file.read()
        if raw_data is None:
            return None

        parsed_data = None
        if self.file_format == DataObjectFileFormat.JSON:
            try:
                parsed_data = json.loads(
                    raw_data, cls=DatetimeAwareJSONDecoder
                )
            except json.JSONDecodeError:
                raise exceptions.InvalidFileFormatError(
                    file_name=self.ea_file.path, file_format="json"
                )
        elif self.file_format == DataObjectFileFormat.YAML:
            try:
                parsed_data = safe_load(raw_data)
            except yaml_parser.ParserError:
                raise exceptions.InvalidFileFormatError(
                    file_name=self.ea_file.path, file_format="yaml"
                )

        if parsed_data is None:
            return None

        if self.preprocess_data:
            parsed_data = self.preprocess_data(parsed_data)

        return self.data_object_cls.from_dict(
            parsed_data,
            optional_type_errors_become_null=self.optional_type_errors_become_null,  # noqa: E501
        )

    def write(self, content: DOFType):
        if self.file_format == DataObjectFileFormat.JSON:
            str_content = content.to_json()
        elif self.file_format == DataObjectFileFormat.YAML:
            data = content.to_dict()
            str_content = safe_dump(data, default_flow_style=False)

        self.ea_file.write(str_content)

    def delete(self):
        self.ea_file.delete()

    @property
    def path(self):
        return self.ea_file.path
