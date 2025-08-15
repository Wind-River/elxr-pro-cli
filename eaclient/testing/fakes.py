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

from eaclient import exceptions, http, messages
from eaclient.contract import EAContractClient


class FakeContractClient(EAContractClient):

    _requests = []
    _responses = {}

    def __init__(self, cfg, responses=None):
        super().__init__(cfg)
        if responses:
            self._responses = responses

    def request_url(
        self, path, data=None, headers=None, method=None, query_params=None
    ):
        request = {
            "path": path,
            "data": data,
            "headers": headers,
            "method": method,
            "query_params": method,
        }
        self._requests.append(request)
        # Return a response if we have one or empty
        response = self._responses.get(path)
        if isinstance(response, http.HTTPResponse):
            return response
        return http.HTTPResponse(
            code=200,
            headers={"header1": ""},
            body="",
            json_dict=response,
            json_list=[],
        )


class FakeFile:
    def __init__(self, content: str, name: str = "fakefile"):
        self.content = content
        self.cursor = 0
        self.name = name

    def read(self, size=None):
        if self.cursor == len(self.content):
            return ""
        if size is None or size >= len(self.content):
            self.cursor = len(self.content)
            return self.content
        ret = self.content[self.cursor : size]
        self.cursor += size
        return ret

    def __enter__(self):
        return self

    def __exit__(self, _exc_type, _exc_value, _traceback):
        pass


class FakeELxrProError(exceptions.ELxrProError):
    _msg = messages.NamedMessage("test-error", "This is a test")
