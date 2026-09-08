from __future__ import annotations

import json
from collections.abc import Mapping
from typing import Any

import requests

from .utils import DnsRecord
from .utils import ExistingDnsRecord


class PorkbunAPI:
    def __init__(self, apikey: str, secretapikey: str, endpoint: str) -> None:
        self._config = {"secretapikey": secretapikey, "apikey": apikey, "endpoint": endpoint}

    def _query_api(
        self, endpoint: str, payload: Mapping[str, Any] | None = None, datafield: str | None = None
    ) -> tuple[Any, bool]:
        if payload is None:
            payload = {}
        data = {**self._config, **payload}

        try:
            r = requests.post(self._config["endpoint"] + endpoint, data=json.dumps(data))
        except requests.RequestException as e:
            return "request raised an exception: " + str(e), False

        if r.status_code == 200:
            response = r.json()
            if "status" in response:
                if response["status"] == "SUCCESS":
                    if datafield is None:
                        return None, True
                    elif datafield in response:
                        return response[datafield], True
                    else:
                        return (
                            f"invalid response from '{endpoint}': '{datafield}' field not found",
                            False,
                        )
                else:
                    return (
                        response["message"]
                        if "message" in response
                        else f"invalid response from '{endpoint}': no error message provided"
                    ), False
            else:
                return (
                    f"invalid response from '{endpoint}': status field not found",
                    False,
                )
        else:
            return (
                f"request to '{endpoint}' failed with {r.status_code} HTTP status code",
                False,
            )

    def list_dns_records(
        self,
        domain: str,
    ) -> list[ExistingDnsRecord]:
        data, success = self._query_api(endpoint=f"dns/retrieve/{domain}", datafield="records")

        if success:
            return data
        else:
            raise RuntimeError("list_dns_records failed: " + data)

    def create_record(self, domain: str, record: DnsRecord) -> str:
        if (
            isinstance(domain, str)
            and len(domain) > 0
            and isinstance(record, dict)
            and all([x in record.keys() for x in ["name", "type", "content"]])
        ):
            data, success = self._query_api(endpoint=f"dns/create/{domain}", payload=record, datafield="id")
        else:
            data = "invalid input values"
            success = False

        if success:
            return data
        else:
            raise RuntimeError("create_record failed: " + data)

    def update_record(self, domain: str, record_id: str, new_record: DnsRecord) -> None:
        if (
            isinstance(domain, str)
            and len(domain) > 0
            and isinstance(new_record, dict)
            and all([x in new_record.keys() for x in ["name", "type", "content"]])
            and record_id is not None
        ):
            data, success = self._query_api(endpoint=f"dns/edit/{domain}/{record_id}", payload=new_record)
        else:
            data = "invalid input values"
            success = False

        if success:
            return None
        else:
            raise RuntimeError("update_record failed: " + data)

    def get_my_ip(self) -> str:
        data, success = self._query_api(endpoint="ping", datafield="yourIp")

        if success:
            return data
        else:
            raise RuntimeError("get_my_ip failed: " + data)
