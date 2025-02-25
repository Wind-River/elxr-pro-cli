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

import logging
import sys

from eaclient import util
from eaclient.messages import BROKEN_YAML_MODULE, MISSING_YAML_MODULE

LOG = logging.getLogger(util.replace_top_level_logger_name(__name__))

try:
    import yaml
except ImportError as e:
    LOG.exception(e)
    print(MISSING_YAML_MODULE, file=sys.stderr)
    sys.exit(1)


def safe_load(stream):
    try:
        return yaml.safe_load(stream)
    except AttributeError as e:
        LOG.exception(e)
        print(BROKEN_YAML_MODULE.format(path=yaml.__path__), file=sys.stderr)
        sys.exit(1)


def safe_dump(data, stream=None, **kwargs):
    try:
        return yaml.safe_dump(data, stream, **kwargs)
    except AttributeError as e:
        LOG.exception(e)
        print(BROKEN_YAML_MODULE.format(path=yaml.__path__), file=sys.stderr)
        sys.exit(1)


parser = yaml.parser
