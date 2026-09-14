import unittest.mock as mock

import pytest

from porkbun_api_cli import utils
from porkbun_api_cli.utils import ApiConfig
from porkbun_api_cli.utils import Config
from porkbun_api_cli.utils import DnsRecord
from porkbun_api_cli.utils import DomainConfig
from porkbun_api_cli.utils import ExistingDnsRecord
from porkbun_api_cli.utils import Operation


@pytest.mark.parametrize(
    ("target", "other"),
    [
        (
            DnsRecord(name="", type="", content="some content"),
            ExistingDnsRecord(name="", type="", id="", content="some content"),
        ),
        (
            DnsRecord(name="", type="", content="some content", ttl=600),
            ExistingDnsRecord(name="", type="", id="", content="some content", ttl=600),
        ),
        (
            DnsRecord(name="", type="", content="some content", prio=0),
            ExistingDnsRecord(name="", type="", id="", content="some content", prio=0),
        ),
        (
            DnsRecord(name="", type="", content="some content", ttl=600, prio=0),
            ExistingDnsRecord(name="", type="", id="", content="some content", ttl=600, prio=0),
        ),
        (
            DnsRecord(name="", type="", content="some content", ttl=0),
            ExistingDnsRecord(name="", type="", id="", content="some content", ttl=600),
        ),
        (
            DnsRecord(name="", type="", content="some content"),
            ExistingDnsRecord(name="", type="", id="", content="some content", prio=10),
        ),
    ],
)
def test_compare_record_by_content_ttl_prio_equal(target, other):
    assert utils.compare_record_by_content_ttl_prio(target, other)


@pytest.mark.parametrize(
    ("target", "other"),
    [
        (
            DnsRecord(name="", type="", content="target content"),
            ExistingDnsRecord(name="", type="", id="", content="other content"),
        ),
        (
            DnsRecord(name="", type="", content="some content", ttl=6),
            ExistingDnsRecord(name="", type="", id="", content="some content", ttl=600),
        ),
        (
            DnsRecord(name="", type="", content="some content", prio=10),
            ExistingDnsRecord(name="", type="", id="", content="some content", prio=0),
        ),
        (
            DnsRecord(name="", type="", content="some content", ttl=6, prio=0),
            ExistingDnsRecord(name="", type="", id="", content="some content", ttl=600, prio=0),
        ),
        (
            DnsRecord(name="", type="", content="some content", ttl=600, prio=10),
            ExistingDnsRecord(name="", type="", id="", content="some content", ttl=600, prio=0),
        ),
        (
            DnsRecord(name="", type="", content="target content", ttl=600, prio=0),
            ExistingDnsRecord(name="", type="", id="", content="other content", ttl=600, prio=0),
        ),
    ],
)
def test_compare_record_by_content_ttl_prio_unequal(target, other):
    assert not utils.compare_record_by_content_ttl_prio(target, other)


@pytest.mark.parametrize(
    ("domain_name", "target", "other"),
    [
        (
            "equal.com",
            DnsRecord(name="", type="A", content=""),
            ExistingDnsRecord(name="equal.com", type="A", id="", content=""),
        ),
        (
            "equal.com",
            DnsRecord(name="www", type="A", content=""),
            ExistingDnsRecord(name="www.equal.com", type="A", id="", content=""),
        ),
        (
            "equal.com",
            DnsRecord(name="mail", type="MX", content=""),
            ExistingDnsRecord(name="mail.equal.com", type="MX", id="", content=""),
        ),
    ],
)
def test_compare_record_by_name_type_equal(domain_name, target, other):
    assert utils.compare_record_by_name_type(domain_name, target, other)


@pytest.mark.parametrize(
    ("domain_name", "target", "other"),
    [
        (
            "unequal.com",
            DnsRecord(name="", type="A", content=""),
            ExistingDnsRecord(name="equal.com", type="A", id="", content=""),
        ),
        (
            "unequal.com",
            DnsRecord(name="", type="A", content=""),
            ExistingDnsRecord(name="unequal.com", type="AAAA", id="", content=""),
        ),
        (
            "unequal.com",
            DnsRecord(name="www", type="A", content=""),
            ExistingDnsRecord(name="equal.com", type="A", id="", content=""),
        ),
        (
            "equal.com",
            DnsRecord(name="www", type="A", content=""),
            ExistingDnsRecord(name="www.unequal.com", type="A", id="", content=""),
        ),
    ],
)
def test_compare_record_by_name_type_unequal(domain_name, target, other):
    assert not utils.compare_record_by_name_type(domain_name, target, other)


def test_existing_dns_record_from_api_filters_unknown_and_warns(capsys):
    raw = {
        "name": "x",
        "type": "A",
        "content": "1",
        "id": "7",
        "ttl": "600",
        "notes": "x",
        "unknown": "z",
    }
    record = ExistingDnsRecord.from_api(raw)
    assert record.ttl == 600
    assert isinstance(record.ttl, int)
    assert record.notes == "x"
    assert record.id == "7"
    assert "unknown" not in {f.name for f in ExistingDnsRecord.__dataclass_fields__.values()}
    captured = capsys.readouterr()
    assert "unknown" in captured.err


def test_existing_dns_record_from_api_coerces_int_ttl(capsys):
    record = ExistingDnsRecord.from_api({
        "name": "x",
        "type": "A",
        "content": "1",
        "id": "7",
        "ttl": 600,
        "notes": None,
    })
    assert record.ttl == 600
    assert isinstance(record.ttl, int)
    assert record.notes is None
    captured = capsys.readouterr()
    assert captured.err == ""


def test_dns_record_from_api_filters_unknown_and_warns(capsys):
    raw = {
        "name": "x",
        "type": "A",
        "content": "1",
        "ttl": "600",
        "notes": "ignored",
        "unknown": "z",
    }
    record = DnsRecord.from_api(raw)
    assert record.ttl == 600
    assert isinstance(record.ttl, int)
    captured = capsys.readouterr()
    assert "unknown" in captured.err
    assert "notes" not in {f.name for f in DnsRecord.__dataclass_fields__.values()}


@pytest.mark.parametrize(
    ("mode", "operation"),
    [
        ("append", "create"),
        ("update", "update"),
        ("upgrade", "create"),
        ("upgrade", "update"),
        ("replace", "create"),
        ("replace", "update"),
        ("replace", "delete"),
    ],
)
def test_operation_allowed_by_mode_allowed(operation, mode):
    assert utils.operation_allowed_by_mode(operation, mode)


@pytest.mark.parametrize(
    ("mode", "operation"),
    [
        ("append", "update"),
        ("append", "delete"),
        ("update", "create"),
        ("update", "delete"),
        ("upgrade", "delete"),
        ("append", "unknown"),
        ("update", "unknown"),
        ("upgrade", "unknown"),
        ("replace", "unknown"),
        ("unknown", "unknown"),
    ],
)
def test_operation_allowed_by_mode_not_allowed(operation, mode):
    assert not utils.operation_allowed_by_mode(operation, mode)


def test_load_config_valid():

    data = (
        "api:\n"
        "  endpoint: 'http://example.com'\n"
        "  apikey: 'mock_apikey'\n"
        "  secretapikey: 'mock_secretapikey'\n"
        "domains:\n"
    )
    expected = Config(
        api=ApiConfig(apikey="mock_apikey", secretapikey="mock_secretapikey", endpoint="http://example.com"),
        domains=[],
    )
    with mock.patch("builtins.open", mock.mock_open(read_data=data)):
        actual = utils.load_config("")
        assert expected == actual


def test_load_config_with_records():

    data = (
        "api:\n"
        "  endpoint: 'http://example.com'\n"
        "  apikey: 'mock_apikey'\n"
        "  secretapikey: 'mock_secretapikey'\n"
        "domains:\n"
        "  - name: example.com\n"
        "    records:\n"
        "      - name: ''\n"
        "        type: A\n"
        "        content: 127.0.0.1\n"
        "      - name: www\n"
        "        type: A\n"
        "        content: 127.0.0.1\n"
        "        ttl: 600\n"
    )
    expected = Config(
        api=ApiConfig(apikey="mock_apikey", secretapikey="mock_secretapikey", endpoint="http://example.com"),
        domains=[
            DomainConfig(
                name="example.com",
                records=[
                    DnsRecord(name="", type="A", content="127.0.0.1"),
                    DnsRecord(name="www", type="A", content="127.0.0.1", ttl=600),
                ],
            ),
        ],
    )
    with mock.patch("builtins.open", mock.mock_open(read_data=data)):
        actual = utils.load_config("")
        assert expected == actual


@pytest.mark.parametrize(
    "data",
    [
        "",
        "api:\n",
        "api:\n  apikey: 'mock_apikey'\n",
        "api:\n  secretapikey: 'mock_secretapikey'\n",
        "api:\n  apikey: 'mock_apikey'\n  secretapikey: 'mock_secretapikey'\n",
        "api:\n  apikey: 'mock_apikey'\ndomains:\n",
        "api:\n  secretapikey: 'mock_secretapikey'\ndomains:\n",
        "api:\n  apikey: 'mock_apikey'\n  secretapikey: 'mock_secretapikey'\n  endpoint: ''\n",
        "api:\ndomains:\n",
        "domains:\n",
    ],
)
def test_load_config_invalid(data):

    with mock.patch("builtins.open", mock.mock_open(read_data=data)):
        with pytest.raises(
            ValueError, match="required objects 'api' and/or 'domain' with all required fields not found"
        ):
            utils.load_config("")


def test_operation_construction():
    op = Operation(operation="create")
    assert op.operation == "create"
    assert op.new is None
    assert op.existing is None


def test_dns_record_rejects_unknown_field():
    with pytest.raises(TypeError):
        DnsRecord(name="x", type="A", content="1", magick="42")


def test_existing_dns_record_construction():
    record = ExistingDnsRecord(name="x", type="A", content="1", id="7", ttl=600, notes="n")
    assert record.name == "x"
    assert record.ttl == 600
    assert record.id == "7"
    assert record.notes == "n"


def test_dns_record_is_frozen():
    from dataclasses import FrozenInstanceError

    record = DnsRecord(name="x", type="A", content="1")
    with pytest.raises(FrozenInstanceError):
        record.ttl = 600  # type: ignore[misc]
