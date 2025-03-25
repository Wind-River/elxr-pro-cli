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

import mock
import pytest

from eaclient import exceptions
from eaclient.data_types import (
    DataObject,
    Field,
    IncorrectFieldTypeError,
    IntDataValue,
    StringDataValue,
)
from eaclient.files.data_types import DataObjectFile, DataObjectFileFormat


class MockEAFile:
    def __init__(self):
        self.write = mock.MagicMock()
        self.read = mock.MagicMock()
        self.delete = mock.MagicMock()
        self.path = mock.MagicMock()


class NestedTestData(DataObject):
    fields = [
        Field("integer", IntDataValue),
    ]

    def __init__(self, integer: int):
        self.integer = integer


class TestData(DataObject):
    __test__ = False
    fields = [
        Field("string", StringDataValue),
        Field("nested", NestedTestData),
    ]

    def __init__(self, string: str, nested: NestedTestData):
        self.string = string
        self.nested = nested


class TestDataObjectFile:
    def test_write_valid_json(self):
        mock_file = MockEAFile()
        dof = DataObjectFile(
            TestData,
            mock_file,
        )
        dof.write(TestData(string="test", nested=NestedTestData(integer=1)))
        assert mock_file.write.call_args_list == [
            mock.call("""{"nested": {"integer": 1}, "string": "test"}""")
        ]

    def test_write_valid_yaml(self):
        mock_file = MockEAFile()
        dof = DataObjectFile(
            TestData,
            mock_file,
            DataObjectFileFormat.YAML,
        )
        dof.write(TestData(string="test", nested=NestedTestData(integer=1)))
        assert mock_file.write.call_args_list == [
            mock.call("""nested:\n  integer: 1\nstring: test\n""")
        ]

    def test_read_valid_json(self):
        mock_file = MockEAFile()
        dof = DataObjectFile(
            TestData,
            mock_file,
        )
        mock_file.read.return_value = (
            """{"string": "test", "nested": {"integer": 1}}"""
        )
        do = dof.read()
        assert do.string == "test"
        assert do.nested.integer == 1

    def test_read_valid_yaml(self):
        mock_file = MockEAFile()
        dof = DataObjectFile(
            TestData,
            mock_file,
            DataObjectFileFormat.YAML,
        )
        mock_file.read.return_value = (
            """nested:\n  integer: 1\nstring: test\n"""
        )
        do = dof.read()
        assert do.string == "test"
        assert do.nested.integer == 1

    def test_read_invalid_data(self):
        mock_file = MockEAFile()
        dof = DataObjectFile(
            TestData,
            mock_file,
        )
        mock_file.read.return_value = """{"nested": {"integer": 1}}"""
        with pytest.raises(IncorrectFieldTypeError):
            dof.read()

    def test_read_invalid_json(self):
        mock_file = MockEAFile()
        dof = DataObjectFile(
            TestData,
            mock_file,
        )
        mock_file.read.return_value = """{"nested": {"""
        with pytest.raises(exceptions.InvalidFileFormatError):
            dof.read()

    def test_read_invalid_yaml(self):
        mock_file = MockEAFile()
        dof = DataObjectFile(
            TestData,
            mock_file,
            DataObjectFileFormat.YAML,
        )
        mock_file.read.return_value = """nested": {"""
        with pytest.raises(exceptions.InvalidFileFormatError):
            dof.read()
