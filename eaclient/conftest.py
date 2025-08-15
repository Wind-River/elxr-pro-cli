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

import io
import logging
import os
import shutil

import mock
import pytest

from eaclient import event_logger
from eaclient.config import EAConfig
from eaclient.files.machine_token import MachineTokenFile
from eaclient.files.user_config_file import UserConfigData


shutil.get_terminal_size = mock.MagicMock(
    return_value=os.terminal_size((80, 20))
)


@pytest.yield_fixture(scope="session", autouse=True)
def _subp():
    """
    A fixture that mocks system._subp for all tests.
    If a test needs the actual _subp, this fixture yields it,
    so just add an argument to the test named "_subp".
    """
    from eaclient.system import _subp

    original = _subp
    with mock.patch(
        "eaclient.system._subp", return_value=("mockstdout", "mockstderr")
    ):
        yield original


@pytest.yield_fixture(scope="session", autouse=True)
def util_we_are_currently_root():
    """
    A fixture that mocks util.we_are_currently_root for all tests.
    Default to true as most tests need it to be true.
    """
    from eaclient.util import we_are_currently_root

    original = we_are_currently_root
    with mock.patch("eaclient.util.we_are_currently_root", return_value=True):
        yield original


@pytest.yield_fixture(scope="session", autouse=True)
def urllib_request_urlopen():
    """
    A fixture that mocks urlopen for all tests.
    This prevents us from accidentally making requests in unit tests
    """
    from urllib.request import urlopen

    original = urlopen
    with mock.patch("urllib.request.urlopen"):
        yield original


@pytest.fixture
def caplog_text(request):
    """
    A fixture that returns a function that returns caplog.text

    caplog isn't available in pytest in all of our target releases; this either
    uses caplog.text if available, or a shim which replicates what it does.

    (It returns a function so that the requester can decide when to examine the
    logs; if it returned caplog.text directly, that would always be empty.)
    """
    cap_params = getattr(request, "param", logging.INFO)
    log_filter = None
    if isinstance(cap_params, tuple):
        log_level = cap_params[0]
        log_filter = cap_params[1]
    else:
        log_level = cap_params
    try:
        try:
            caplog = request.getfixturevalue("caplog")
        except AttributeError:
            # Older versions of pytest only have getfuncargvalue, which is now
            # deprecated in favour of getfixturevalue
            caplog = request.getfuncargvalue("caplog")
        caplog.set_level(log_level)
        if log_filter:
            caplog.handler.addFilter(log_filter())

        def _func():
            return caplog.text

    except LookupError:
        # If the caplog fixture isn't available, shim something in ourselves
        root = logging.getLogger("elxr-pro")
        root.propagate = False
        root.setLevel(log_level)
        handler = logging.StreamHandler(io.StringIO())
        handler.setFormatter(
            logging.Formatter(
                "%(filename)-25s %(lineno)4d %(levelname)-8s %(message)s"
            )
        )
        if log_filter:
            handler.addFilter(log_filter())
        root.addHandler(handler)

        def _func():
            return handler.stream.getvalue()

        def clear_handlers():
            root.handlers = []

        request.addfinalizer(clear_handlers)
    return _func


@pytest.yield_fixture
def logging_sandbox():
    # Monkeypatch a replacement root logger, so that our changes to logging
    # configuration don't persist outside of the test
    epro_logger = logging.getLogger("elxr-pro")
    epro_logger.setLevel(logging.WARNING)

    with mock.patch.object(logging, "root", epro_logger):
        with mock.patch.object(logging.Logger, "root", epro_logger):
            with mock.patch.object(
                logging.Logger, "manager", logging.Manager(epro_logger)
            ):
                yield


@pytest.yield_fixture(scope="function", autouse=True)
def fake_machine_token_file():
    from unittest.mock import patch

    with patch(
        "eaclient.files.machine_token.get_machine_token_file"
    ) as m_get_machine_token_file:
        machine_token = FakeMachineToken(attached=False)
        m_get_machine_token_file.return_value = machine_token
        yield machine_token


class FakeMachineToken(MachineTokenFile):
    def __init__(self, attached, token=None):
        self.attached = attached
        self._machine_token = None
        self.token = token
        self._contract_expiry_datetime = None
        self._entitlements = None
        self.write_calls = 0
        self.delete_calls = 0

    @property
    def machine_token(self):
        self._machine_token = None
        return super().machine_token

    @property
    def is_present(self):
        return self.attached

    def read(self):
        if self.token:
            return self.token

        if not self.attached:
            return None

        return {
            "machineId": "test_machine_id",
            "token": "not-full",
            "machineInfo": {
                "distribution": "elxr12",
                "kernel": "6.1.123-1",
                "series": "aria",
                "architecture": "amd64",
                "desktop": True,
                "virt": "",
                "clientVersion": "1.0.0"
            },
        }

    def write(self, private_content):
        self.token = private_content
        self.write_calls += 1

    def delete(self):
        self.delete_calls += 1


@pytest.fixture
def FakeConfig(tmpdir):
    class _FakeConfig(EAConfig):
        def __init__(
            self,
            cfg_overrides={},
            features_override=None,
        ) -> None:
            if not cfg_overrides.get("data_dir"):
                cfg_overrides.update({"data_dir": tmpdir.strpath})
            if not cfg_overrides.get("log_file"):
                cfg_overrides.update(
                    {"log_file": tmpdir.join("log_file.log").strpath}
                )
            super().__init__(
                cfg_overrides,
                user_config=UserConfigData(),
            )

    return _FakeConfig


@pytest.fixture
def event():
    event = event_logger.get_event_logger()
    event.reset()

    return event


@pytest.fixture(autouse=True)
def disable_warn_about_non_elxr(monkeypatch):
    monkeypatch.setattr(
        "eaclient.cli.warn_about_non_elxr_distro",
        lambda: None
    )
