import abc
import json
import posixpath
from typing import Any, Dict, Optional  # noqa: F401
from urllib.parse import urlencode

from eaclient import config, http, util, version


class EAServiceClient(metaclass=abc.ABCMeta):

    url_timeout = 30  # type: Optional[int]
    # Cached serviceclient_url_responses if provided in eaclient.conf
    # via features: {serviceclient_url_responses: /some/file.json}
    _response_overlay = None  # type: Dict[str, Any]

    @property
    @abc.abstractmethod
    def cfg_url_base_attr(self) -> str:
        """String in subclasses, the EAConfig attribute containing base url"""
        pass

    def __init__(self, cfg: Optional[config.EAConfig] = None) -> None:
        if not cfg:
            self.cfg = config.EAConfig()
        else:
            self.cfg = cfg

    def headers(self):
        return {
            "user-agent": "EA-Client/{}".format(version.get_version()),
            "accept": "application/json",
            "content-type": "application/json",
        }

    def request_url(
        self,
        path,
        data=None,
        headers=None,
        method=None,
        query_params=None,
        log_response_body: bool = True,
        timeout: Optional[int] = None,
    ) -> http.HTTPResponse:
        path = path.lstrip("/")
        if not headers:
            headers = self.headers()
        if headers.get("content-type") == "application/json" and data:
            data = json.dumps(data, cls=util.DatetimeAwareJSONEncoder).encode(
                "utf-8"
            )
        url = posixpath.join(getattr(self.cfg, self.cfg_url_base_attr), path)

        if query_params:
            # filter out None values
            filtered_params = {
                k: v for k, v in sorted(query_params.items()) if v is not None
            }
            url += "?" + urlencode(filtered_params)
        timeout_to_use = timeout if timeout is not None else self.url_timeout

        return http.readurl(
            url=url,
            data=data,
            headers=headers,
            method=method,
            timeout=timeout_to_use,
            log_response_body=log_response_body,
        )
