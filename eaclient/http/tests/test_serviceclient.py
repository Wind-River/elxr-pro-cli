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

from urllib.parse import urlencode

import mock
import pytest

from eaclient.http.serviceclient import EAServiceClient


class OurServiceClient(EAServiceClient):
    @property
    def cfg_url_base_attr(self):
        return "contract_url"


class TestRequestUrl:

    # TODO: Non error-path tests

    @pytest.mark.parametrize(
        "m_kwargs", ({"a": 1, "b": "2", "c": "try me"}, {})
    )
    @mock.patch("eaclient.http.readurl")
    def test_url_query_params_append_querystring(
        self, m_readurl, m_kwargs, FakeConfig
    ):
        m_readurl.return_value = (m_kwargs, {})  # (response, resp_headers)

        cfg = FakeConfig()
        url = "http://example.com/"
        cfg.cfg["contract_url"] = url
        client = OurServiceClient(cfg=cfg)
        assert (m_kwargs, {}) == client.request_url("/", query_params=m_kwargs)
        if m_kwargs:
            url += "?" + urlencode(m_kwargs)
        assert [
            mock.call(
                url=url,
                data=None,
                headers=client.headers(),
                method=None,
                timeout=30,
                log_response_body=True,
            )
        ] == m_readurl.call_args_list
