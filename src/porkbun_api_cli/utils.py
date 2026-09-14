from __future__ import annotations

import sys
from dataclasses import dataclass
from dataclasses import fields
from typing import Any
from typing import Literal

import yaml


@dataclass(frozen=True)
class DnsRecord:
    name: str
    type: str
    content: str
    ttl: int | None = None
    prio: int | None = None

    @classmethod
    def from_api(cls, raw: dict[str, Any]) -> DnsRecord:
        known = {f.name for f in fields(cls)}
        for key in raw.keys() - known:
            print(f"warning: unknown field {key!r} in {cls.__name__} payload", file=sys.stderr)
        kwargs: dict[str, Any] = {k: raw[k] for k in raw if k in known}
        if raw.get("ttl") is not None:
            kwargs["ttl"] = int(raw["ttl"])
        if raw.get("prio") is not None:
            kwargs["prio"] = int(raw["prio"])
        return cls(**kwargs)


@dataclass(frozen=True)
class ExistingDnsRecord:
    name: str
    type: str
    content: str
    id: str
    ttl: int | None = None
    prio: int | None = None
    notes: str | None = None

    @classmethod
    def from_api(cls, raw: dict[str, Any]) -> ExistingDnsRecord:
        known = {f.name for f in fields(cls)}
        for key in raw.keys() - known:
            print(f"warning: unknown field {key!r} in {cls.__name__} payload", file=sys.stderr)
        kwargs: dict[str, Any] = {k: raw[k] for k in raw if k in known}
        if raw.get("ttl") is not None:
            kwargs["ttl"] = int(raw["ttl"])
        if raw.get("prio") is not None:
            kwargs["prio"] = int(raw["prio"])
        return cls(**kwargs)


@dataclass(frozen=True)
class Operation:
    operation: Literal["create", "update", "delete", "match"]
    new: DnsRecord | None = None
    existing: ExistingDnsRecord | None = None


PlanEntry = Operation


@dataclass(frozen=True)
class ApiConfig:
    apikey: str
    secretapikey: str
    endpoint: str


@dataclass(frozen=True)
class DomainConfig:
    name: str
    records: list[DnsRecord]


@dataclass(frozen=True)
class Config:
    api: ApiConfig
    domains: list[DomainConfig]


def compare_record_by_content_ttl_prio(target: DnsRecord, other: ExistingDnsRecord) -> bool:
    """Compare a record from current configuration and an existing one returned by the API.
    Only consider record content, TTL and priority.

    :param target: target DNS record
    :type target: DnsRecord
    :param other: existing DNS record
    :type other: ExistingDnsRecord
    :returns: True if respective subfields are equal, False otherwise
    :rtype: bool"""
    return (
        target.content == other.content
        and (target.ttl is None or target.ttl == 0 or target.ttl == other.ttl)
        and (target.prio is None or target.prio == other.prio)
    )


def compare_record_by_name_type(domain_name: str, target: DnsRecord, other: ExistingDnsRecord) -> bool:
    """Compare a record from current configuration and an existing one returned by the API.
    Only consider fqdn and record type.

    :param domain_name: domain name
    :type domain_name: str
    :param target: target DNS record
    :type target: DnsRecord
    :param other: existing DNS record
    :type other: ExistingDnsRecord
    :returns: True if respective subfields are equal, False otherwise
    :rtype: bool"""
    target_fqdn = f"{target.name}.{domain_name}" if len(target.name) else domain_name
    return target_fqdn == other.name and target.type == other.type


def operation_allowed_by_mode(operation: str, mode: str) -> bool:
    """Check whether an operation is allowed by current operation mode. Supported operations:

    * create
    * replace
    * update
    * upgrade

    :param operation: operation name
    :type operation: str
    :param mode: current operation mode
    :type mode: str
    :returns: True if operation is allowed, False otherwise
    :rtype: bool"""
    if mode == "append":
        return operation == "create"
    elif mode == "update":
        return operation == "update"
    elif mode == "upgrade":
        return operation in ["create", "update"]
    elif mode == "replace":
        return operation in ["create", "update", "delete"]
    return False


def load_config(config_file_path: str) -> Config:
    """Load configuration from a YAML file with following format:

    :: code_block::yaml
       api:
         endpoint: str # API endpoint URI
         apikey: str # API key
         secretapikey: str # secret API key

       domains:
         - name: str
           records:
             - name: str # subdomain name, e.g., "", www, mail, etc
               type: enum[A, AAAA, CNAME, MX, NS, PTR, SRV, SOA, TXT, CAA, DS, DNSKEY]
               content: str # record value, e.g. IP address

    :param config_file_path: path to configuration file
    :type config_file_path: str
    :returns: configuration dataclass
    :rtype: Config"""

    # Load the YAML configuration file
    with open(config_file_path, "r", encoding="utf-8") as config_file:
        config = yaml.safe_load(config_file)

    if (
        config is None
        or any(x not in config for x in ["api", "domains"])
        or config["api"] is None
        or any(x not in config["api"] for x in ["apikey", "secretapikey", "endpoint"])
    ):
        raise ValueError("required objects 'api' and/or 'domain' with all required fields not found")

    if config["domains"] is None:
        config["domains"] = []

    api_config = ApiConfig(
        apikey=config["api"]["apikey"],
        secretapikey=config["api"]["secretapikey"],
        endpoint=config["api"]["endpoint"],
    )
    domains = [
        DomainConfig(
            name=d["name"],
            records=[DnsRecord(**r) for r in d["records"]],
        )
        for d in config["domains"]
    ]
    return Config(api=api_config, domains=domains)
