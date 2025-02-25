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

from typing import List


class SecretManager:
    def __init__(self):
        self._secrets = []

    def add_secret(self, secret: str) -> None:
        if secret:  # Add only non-empty secrets
            self._secrets.append(secret)

    @property
    def secrets(self) -> List[str]:
        return self._secrets

    def clear_secrets(self) -> None:
        self._secrets.clear()

    def redact_secrets(self, log_record: str) -> str:
        redacted_record = log_record
        for secret in self._secrets:
            redacted_record = redacted_record.replace(secret, "<REDACTED>")
        return redacted_record


secrets = SecretManager()
