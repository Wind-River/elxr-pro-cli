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
import logging
import sys
from io import StringIO

import mock
import pytest

from eaclient import log, util

LOG = logging.getLogger(util.replace_top_level_logger_name(__name__))
LOG_FMT = "%(asctime)s%(name)s%(funcName)s%(lineno)s\
%(levelname)s%(message)s%(extra)s"
DATE_FMT = "%Y-%m-%dT%H:%M:%S%z"


class TestLogger:
    def test_unredacted_text(self, caplog):
        text = "Bearer SEKRET"
        LOG.setLevel(logging.INFO)
        LOG.info(text)
        log_text = caplog.text
        assert text in log_text

    @pytest.mark.parametrize(
        "raw_log,expected",
        (
            ("Super valuable", "Super valuable"),
            (
                "Hi 'Bearer not the droids you are looking for', data",
                "Hi 'Bearer <REDACTED>', data",
            ),
            (
                "Hi 'Bearer not the droids you are looking for', data",
                "Hi 'Bearer <REDACTED>', data",
            ),
            (
                "Executed with sys.argv:"
                " ['/usr/bin/elxr-pro', 'join', 'SEKRET']",
                "Executed with sys.argv:"
                " ['/usr/bin/elxr-pro', 'join', '<REDACTED>']",
            ),
            (
                "Executed with sys.argv:"
                " ['/usr/bin/elxr-pro', 'test', 'SEKRET']",
                "Executed with sys.argv:"
                " ['/usr/bin/elxr-pro', 'test', '<REDACTED>']",
            ),
            (
                "'machineToken': 'SEKRET', 'machineTokenInfo': 'blah'",
                "'machineToken': '<REDACTED>', 'machineTokenInfo': 'blah'",
            ),
            (
                "Contract value for 'resourceToken' changed to S3kR3T",
                "Contract value for 'resourceToken' changed to <REDACTED>",
            ),
            (
                "data: {'contractToken': 'SEKRET', "
                "'machineInfo':{'expiry'}}",
                "data: {'contractToken': '<REDACTED>', "
                "'machineInfo':{'expiry'}}",
            ),
            (
                "data: {'productToken': 'SEKRET', "
                "'entitlement': {'affordances':'blah blah' }}",
                "data: {'productToken': '<REDACTED>', "
                "'entitlement': {'affordances':'blah blah' }}",
            ),
            (
                'data: {"identityToken": "SEket.124-_ys"}',
                'data: {"identityToken": "<REDACTED>"}',
            ),
            (
                "http://elxr.pro/api/v1/actions/join, data: none",
                "http://elxr.pro/api/v1/actions/join, data: none",
            ),
            (
                "response: "
                "http://elxr.pro/api/v1/actions/join, data: none",
                "response: "
                "http://elxr.pro/api/v1/actions/join, data: <REDACTED>",
            ),
            (
                "'token': 'SEKRET'",
                "'token': '<REDACTED>'",
            ),
            (
                "'userCode': 'SEKRET'",
                "'userCode': '<REDACTED>'",
            ),
        ),
    )
    def test_redacted_text(self, caplog, raw_log, expected):
        LOG.setLevel(logging.INFO)
        LOG.addFilter(log.RegexRedactionFilter())
        LOG.info(raw_log)
        log_text = caplog.text
        assert expected in log_text


class TestLoggerFormatter:
    @pytest.mark.parametrize(
        "message,level,log_fn,levelname,extra",
        (
            ("mIDValue", logging.DEBUG, LOG.debug, "DEBUG", None),
            ("2B||~2B", logging.INFO, LOG.info, "INFO", None),
            (
                "2B||~2B",
                logging.WARNING,
                LOG.warning,
                "WARNING",
                {"key": "value"},
            ),
        ),
    )
    def test_valid_json_output(
        self, caplog, message, level, log_fn, levelname, extra
    ):
        formatter = log.JsonArrayFormatter(LOG_FMT, DATE_FMT)
        buffer = StringIO()
        sh = logging.StreamHandler(buffer)
        sh.setLevel(level)
        sh.setFormatter(formatter)
        LOG.setLevel(logging.DEBUG)
        LOG.addHandler(sh)
        log_fn(message, extra={"extra": extra})
        logged_value = buffer.getvalue()
        val = json.loads(logged_value)
        assert val[1] == levelname
        assert val[2] == util.replace_top_level_logger_name(__name__)
        assert val[5] == message
        if extra:
            assert val[6].get("key") == extra.get("key")
        else:
            assert 7 == len(val)


class TestLogHelpers:
    @pytest.mark.parametrize(
        [
            "we_are_currently_root",
            "expected",
        ],
        [
            (True, "cfg_log_file"),
            (False, "user_log_file"),
        ],
    )
    @mock.patch(
        "eaclient.log.get_user_log_file",
        return_value="user_log_file",
    )
    @mock.patch(
        "eaclient.config.EAConfig.log_file",
        new_callable=mock.PropertyMock,
        return_value="cfg_log_file",
    )
    @mock.patch("eaclient.util.we_are_currently_root")
    def test_get_user_or_root_log_file_path(
        self,
        m_we_are_currently_root,
        m_cfg_log_file,
        m_get_user_log_file,
        we_are_currently_root,
        expected,
    ):
        """
        Tests that the correct log_file path is retrieved
        when the user is root and non-root
        """
        m_we_are_currently_root.return_value = we_are_currently_root
        result = log.get_user_or_root_log_file_path()
        # ensure mocks are used properly
        assert m_cfg_log_file.call_count + m_get_user_log_file.call_count == 1
        if we_are_currently_root:
            assert m_cfg_log_file.call_count == 1
        else:
            assert m_get_user_log_file.call_count == 1
        # ensure correct log_file path is returned
        assert expected == result


@mock.patch("eaclient.log.logging.FileHandler")
@mock.patch("eaclient.log.pathlib.Path")
@mock.patch("eaclient.log.logging.getLogger")
class TestSetupCliLogging:
    def test_correct_handlers_added_to_logger(
        self,
        m_getLogger,
        m_path,
        m_FileHandler,
    ):
        fake_logger = mock.MagicMock(
            handlers=[logging.StreamHandler(sys.stderr)]
        )
        m_getLogger.return_value = fake_logger
        fake_file_handler = mock.MagicMock()
        m_FileHandler.return_value = fake_file_handler

        log.setup_cli_logging(11, "fakefile")
        assert len(fake_logger.handlers) == 0  # handlers is cleared
        assert [mock.call(11)] == fake_file_handler.setLevel.call_args_list
        assert [
            mock.call(fake_file_handler)
        ] == fake_logger.addHandler.call_args_list

    def test_log_file_created_if_not_present(
        self, m_getLogger, m_path, m_FileHandler
    ):
        m_path.return_value.exists.return_value = False
        log.setup_cli_logging(logging.INFO, "fakefile")
        assert m_path.return_value.touch.call_args_list == [
            mock.call(mode=0o640)
        ]
