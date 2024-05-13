import unittest.mock as mock

import pytest

from porkbun_api_cli import utils


@pytest.mark.parametrize(
    ("target", "other"),
    [
        ({"content": "some content"}, {"content": "some content"}),
        ({"content": "some content", "ttl": 600}, {"content": "some content", "ttl": 600}),
        ({"content": "some content", "prio": 0}, {"content": "some content", "prio": 0}),
        ({"content": "some content", "ttl": 600, "prio": 0}, {"content": "some content", "ttl": 600, "prio": 0}),
    ],
)
def test_compare_record_by_content_ttl_prio_equal(target, other):
    assert utils.compare_record_by_content_ttl_prio(target, other)


@pytest.mark.parametrize(
    ("target", "other"),
    [
        ({"content": "target content"}, {"content": "other content"}),
        ({"content": "some content", "ttl": 6}, {"content": "some content", "ttl": 600}),
        ({"content": "some content", "prio": 10}, {"content": "some content", "prio": 0}),
        ({"content": "some content", "ttl": 6, "prio": 0}, {"content": "some content", "ttl": 600, "prio": 0}),
        ({"content": "some content", "ttl": 600, "prio": 10}, {"content": "some content", "ttl": 600, "prio": 0}),
        ({"content": "target content", "ttl": 600, "prio": 0}, {"content": "other content", "ttl": 600, "prio": 0}),
    ],
)
def test_compare_record_by_content_ttl_prio_unequal(target, other):
    assert not utils.compare_record_by_content_ttl_prio(target, other)


@pytest.mark.parametrize(
    ("domain_name", "target", "other"),
    [
        ("equal.com", {"name": "", "type": "A"}, {"name": "equal.com", "type": "A"}),
        ("equal.com", {"name": "www", "type": "A"}, {"name": "www.equal.com", "type": "A"}),
        ("equal.com", {"name": "mail", "type": "MX"}, {"name": "mail.equal.com", "type": "MX"}),
    ],
)
def test_compare_record_by_name_type_equal(domain_name, target, other):
    assert utils.compare_record_by_name_type(domain_name, target, other)


@pytest.mark.parametrize(
    ("domain_name", "target", "other"),
    [
        ("unequal.com", {"name": "", "type": "A"}, {"name": "equal.com", "type": "A"}),
        ("unequal.com", {"name": "", "type": "A"}, {"name": "unequal.com", "type": "AAAA"}),
        ("unequal.com", {"name": "www", "type": "A"}, {"name": "equal.com", "type": "A"}),
        ("equal.com", {"name": "www", "type": "A"}, {"name": "www.unequal.com", "type": "A"}),
    ],
)
def test_compare_record_by_name_type_unequal(domain_name, target, other):
    assert not utils.compare_record_by_name_type(domain_name, target, other)


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

    data = "api:\n  apikey: 'mock_apikey'\n  secretapikey: 'mock_secretapikey'\ndomains:\n"
    expected = {"api": {"apikey": "mock_apikey", "secretapikey": "mock_secretapikey"}, "domains": []}
    with mock.patch("builtins.open", mock.mock_open(read_data=data)):
        # with pytest.raises(ValueError, match="required object 'database' with all required fields not found"):
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
