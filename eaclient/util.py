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
import json
import logging
import os
import re
import time
from functools import wraps
from typing import Any, Dict, List, Optional, Union  # noqa: F401

from eaclient import messages


def replace_top_level_logger_name(name: str) -> str:
    """Replace the name of the root logger from __name__"""
    if name == "":
        return ""
    names = name.split(".")
    names[0] = "elxr-pro"
    return ".".join(names)


LOG = logging.getLogger(replace_top_level_logger_name(__name__))


class DatetimeAwareJSONEncoder(json.JSONEncoder):
    """A json.JSONEncoder subclass that writes out isoformat'd datetimes."""

    def default(self, o):
        if isinstance(o, datetime.datetime):
            return o.isoformat()
        return super().default(o)


class DatetimeAwareJSONDecoder(json.JSONDecoder):
    """
    A JSONDecoder that parses some ISO datetime strings to datetime objects.

    Important note: the "some" is because we seem to only be able extend
    Python's json library in a way that lets us convert string values within
    JSON objects (e.g. '{"lastModified": "2019-07-25T14:35:51"}'). Strings
    outside of JSON objects (e.g. '"2019-07-25T14:35:51"') will not be passed
    through our decoder.

    (N.B. This will override any object_hook specified using arguments to it,
    or used in load or loads calls that specify this as the cls.)
    """

    def __init__(self, *args, **kwargs):
        if "object_hook" in kwargs:
            kwargs.pop("object_hook")
        super().__init__(*args, object_hook=self.object_hook, **kwargs)

    @staticmethod
    def object_hook(o):
        for key, value in o.items():
            if isinstance(value, str):
                try:
                    new_value = parse_rfc3339_date(
                        value
                    )  # type: Union[str, datetime.datetime]
                except ValueError:
                    # This isn't a string containing a valid ISO 8601 datetime
                    new_value = value
                o[key] = new_value
        return o


def retry(exception, retry_sleeps):
    """Decorator to retry on exception for retry_sleeps.

    @param retry_sleeps: List of sleep lengths to apply between
       retries. Specifying a list of [0.5, 1] tells subp to retry twice
       on failure; sleeping half a second before the first retry and 1 second
       before the second retry.
    @param exception: The exception class to catch and retry for the provided
       retry_sleeps. Any other exception types will not be caught by the
       decorator.
    """

    def wrapper(f):
        @wraps(f)
        def decorator(*args, **kwargs):
            sleeps = retry_sleeps.copy()
            while True:
                try:
                    return f(*args, **kwargs)
                except exception as e:
                    if not sleeps:
                        raise e
                    LOG.debug(
                        "%s: Retrying %d more times.", str(e), len(sleeps)
                    )
                    time.sleep(sleeps.pop(0))

        return decorator

    return wrapper


def prompt_for_confirmation(
    msg: str = "", assume_yes: bool = False, default: bool = False
) -> bool:
    """
    Display a confirmation prompt, returning a bool indicating the response

    :param msg: String custom prompt text to emit from input call.
    :param assume_yes: Boolean set True to skip confirmation input and return
        True.
    :param default: Boolean to return when user doesn't enter any text

    This function will only prompt a single time, and defaults to "no" (i.e. it
    returns False).
    """
    if assume_yes:
        return True
    if not msg:
        msg = messages.PROMPT_YES_NO
    value = input(msg).lower().strip()
    if value == "":
        return default
    if value in ["y", "yes"]:
        return True
    return False


REDACT_SENSITIVE_LOGS = [
    r"(Bearer )[^\']+",
    r"(\'join\', \')[^\']+",
    r"(\'test\', \')[^\']+",
    r"(\'machineToken\': \')[^\']+",
    r"(\'productToken\': \')[^\']+",
    r"(\'token\': \')[^\']+",
    r"(\'X-aws-ec2-metadata-token\': \')[^\']+",
    r"(.*\[PUT\] response.*api/token,.*data: ).*",
    r"(https://bearer:)[^\@]+",
    r"(Contract\s+value\s+for\s+'resourceToken'\s+changed\s+to\s+).*",
    r"(\'resourceToken\': \')[^\']+",
    r"(\'contractToken\': \')[^\']+",
    r"(\"identityToken\": \")[^\"]+",
    r"(response:\s+http://elxr.pro/api/v1/actions/join.*data: ).*",
    r"(\'token\': \')[^\']+",
    r"(\'userCode\': \')[^\']+",
    r"(\'magic_token=)[^\']+",
    r"(--registration-key=\")[^\"]+",
    r"(--registration-key=\')[^\']+",
    r"(--registration-key=)[^ ]+",
    r"(--registration-key \")[^\"]+",
    r"(--registration-key \')[^\']+",
    r"(--registration-key )[^\s]+",
    r"(-p \")[^\"]+",
    r"(-p \')[^\']+",
    r"(-p )[^\s]+",
]


def redact_sensitive_logs(
    log, redact_regexs: List[str] = REDACT_SENSITIVE_LOGS
) -> str:
    """Redact known sensitive information from log content."""
    redacted_log = log
    for redact_regex in redact_regexs:
        redacted_log = re.sub(redact_regex, r"\g<1><REDACTED>", redacted_log)
    return redacted_log


def parse_rfc3339_date(dt_str: str) -> datetime.datetime:
    """
    Parse a datestring in rfc3339 format. Originally written for compatibility
    with golang's time.MarshalJSON function. Also handles output of pythons
    isoformat datetime method.

    This drops subseconds.

    :param dt_str: a date string in rfc3339 format

    :return: datetime.datetime object of time represented by dt_str
    """
    # remove sub-seconds
    # Examples:
    #   Before: "2001-02-03T04:05:06.123456"
    #   After: "2001-02-03T04:05:06"
    #   Before: "2001-02-03T04:05:06.123456Z"
    #   After: "2001-02-03T04:05:06Z"
    #   Before: "2001-02-03T04:05:06.123456+09:00"
    #   After: "2001-02-03T04:05:06+09:00"
    dt_str_without_subseconds = re.sub(
        r"(\d{2}:\d{2}:\d{2})\.\d+", r"\g<1>", dt_str
    )
    # if there is no timezone info, assume UTC
    # Examples:
    #   Before: "2001-02-03T04:05:06"
    #   After: "2001-02-03T04:05:06Z"
    #   Before: "2001-02-03T04:05:06Z"
    #   After: "2001-02-03T04:05:06Z"
    #   Before: "2001-02-03T04:05:06+09:00"
    #   After: "2001-02-03T04:05:06+09:00"
    dt_str_with_z = re.sub(
        r"(\d{2}:\d{2}:\d{2})$", r"\g<1>Z", dt_str_without_subseconds
    )
    # replace Z with offset for UTC
    # Examples:
    #   Before: "2001-02-03T04:05:06Z"
    #   After: "2001-02-03T04:05:06+00:00"
    #   Before: "2001-02-03T04:05:06+09:00"
    #   After: "2001-02-03T04:05:06+09:00"
    dt_str_without_z = dt_str_with_z.replace("Z", "+00:00")
    # change offset format to not include colon `:`
    # Examples:
    #   Before: "2001-02-03T04:05:06+00:00"
    #   After: "2001-02-03T04:05:06+0000"
    #   Before: "2001-02-03T04:05:06+09:00"
    #   After: "2001-02-03T04:05:06+0900"
    dt_str_with_pythonish_tz = re.sub(
        r"(-|\+)(\d{2}):(\d{2})$", r"\g<1>\g<2>\g<3>", dt_str_without_z
    )
    return datetime.datetime.strptime(
        dt_str_with_pythonish_tz, "%Y-%m-%dT%H:%M:%S%z"
    )


def we_are_currently_root() -> bool:
    return os.getuid() == 0


def get_pro_environment():
    return {
        k: v
        for k, v in os.environ.items()
    }
