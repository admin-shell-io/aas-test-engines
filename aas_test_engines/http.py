from typing import Tuple, Optional, List, Dict
import requests
from requests.models import Response
from dataclasses import dataclass, field
from urllib.parse import urlencode
import json


@dataclass
class Request:
    path: str
    method: str = "get"
    body: any = None
    query_parameters: dict = field(default_factory=dict)
    headers: dict = field(default_factory=dict)
    cookies: dict = field(default_factory=dict)

    def make_url(self) -> str:
        url = self.path
        query_params = {k: v for k, v in self.query_parameters.items() if v is not None}
        if query_params:
            url += "?" + urlencode(query_params)
        return url

    def dump(self, body_max_chars=80):
        print(f"{self.method.upper()} {self.make_url()}")
        if self.body is not None:
            body_json = json.dumps(self.body)
            if len(body_json) > body_max_chars:
                b = body_json[:body_max_chars] + "..."
            else:
                b = body_json
            print(f"  BODY: {b}")


class HttpClient:

    def __init__(
        self, host: str, verify: bool = False, remove_path_prefix: str = "", additional_headers: Dict[str, str] = {}
    ):
        self.host = host
        self.verify = verify
        self.remove_path_prefix = remove_path_prefix
        self.prefixes: List[str] = []
        self.additional_headers = additional_headers

    def descend(self, prefix: str):
        result = HttpClient(self.host, self.verify, self.remove_path_prefix, self.additional_headers)
        result.prefixes.append(prefix)
        return result

    def send(self, request: Request) -> Response:
        if request.body is None:
            body = None
        else:
            body = json.dumps(request.body)

        if self.host.endswith("/"):
            host = self.host[:-1]
        else:
            host = self.host

        url = "".join(self.prefixes) + request.make_url()
        if url.startswith(self.remove_path_prefix) and (
            len(url) == len(self.remove_path_prefix) or url[len(self.remove_path_prefix)] == "/"
        ):
            url = url[len(self.remove_path_prefix) :]

        return requests.request(
            url=host + url,
            method=request.method,
            data=body,
            headers=request.headers,
            verify=self.verify,
        )
