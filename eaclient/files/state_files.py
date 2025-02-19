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
