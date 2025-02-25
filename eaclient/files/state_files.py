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

from eaclient import defaults
from eaclient.data_types import (
    DataObject,
    DatetimeDataValue,
    Field,
)

from eaclient.files.data_types import DataObjectFile, DataObjectFileFormat
from eaclient.files.files import EAFile


class AttachmentData(DataObject):
    fields = [
        Field("attached_at", DatetimeDataValue),
    ]

    def __init__(self, attached_at: datetime.datetime):
        self.attached_at = attached_at


attachment_data_file = DataObjectFile(
    AttachmentData,
    EAFile("attachment.json", private=False),
    DataObjectFileFormat.JSON,
)


machine_id_file = EAFile(
    "machine-id",
    defaults.DEFAULT_PRIVATE_DATA_DIR,
    private=True,
)


def delete_state_files():
    machine_id_file.delete()
    attachment_data_file.delete()
