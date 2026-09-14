import sys
from unittest import TestCase
from unittest.mock import Mock
from unittest.mock import call
from unittest.mock import patch

import pytest
from click.testing import CliRunner

from porkbun_api_cli import __version__
from porkbun_api_cli import api
from porkbun_api_cli import cli
from porkbun_api_cli.utils import DnsRecord
from porkbun_api_cli.utils import ExistingDnsRecord
from porkbun_api_cli.utils import Operation
from porkbun_api_cli.utils import PlanEntry


@pytest.fixture
def runner():
    return CliRunner()


def test_cli_no_args(runner):
    result = runner.invoke(cli.main)
    assert result.exit_code == 2
    assert result.exception
    assert result.output.strip().startswith('Usage: ')


def test_cli_usage(runner):
    result = runner.invoke(cli.main, ['--help'])
    assert result.exit_code == 0
    assert not result.exception
    assert result.output.strip().startswith('Usage: ')


def test_cli_version(runner):
    result = runner.invoke(cli.main, ['--version'])
    assert result.exit_code == 0
    assert not result.exception
    assert result.output.strip() == f'Version {__version__}'


def test_cli_dry_run(runner, monkeypatch):
    mock_api = Mock()
    monkeypatch.setattr(api, "PorkbunAPI", mock_api)
    mock_api().get_my_ip.return_value = "some-ip-address"

    mock_collect_existing_dns_records = Mock()
    monkeypatch.setattr(cli, '_collect_existing_dns_records', mock_collect_existing_dns_records)
    mock_collect_existing_dns_records.return_value = "existing-records"

    mock_plan_operations = Mock()
    monkeypatch.setattr(cli, '_plan_operations', mock_plan_operations)

    mock_execute_operations_plan = Mock()
    monkeypatch.setattr(cli, '_execute_operations_plan', mock_execute_operations_plan)

    result = runner.invoke(cli.main, ['tests/config.yml', '--dry-run'])

    print(f"output : '{result.output.strip()}'")

    assert result.exit_code == 0
    assert not result.exception
    assert result.output.strip() == '\n'.join([
        "dry run requested, enable verbose output",
        "IP address reported by API 'some-ip-address'",
        "dry run requested, skipping execution",
    ])

    # Assertions on calls
    mock_collect_existing_dns_records.assert_called_once_with(mock_api(), ["example.com"], 2)
    mock_plan_operations.assert_called_once_with(
        "append",
        2,
        "existing-records",
        {
            'example.com': [
                DnsRecord(name='', type='A', content='192.168.192.168'),
                DnsRecord(name='autoconfig', type='A', content='192.168.192.168'),
                DnsRecord(name='git', type='A', content='192.168.192.168'),
                DnsRecord(name='mail', type='A', content='192.168.192.168'),
                DnsRecord(name='www', type='A', content='192.168.192.168'),
                DnsRecord(name='', type='MX', content='mail.example.com'),
                DnsRecord(name='', type='TXT', content='mock entry 1'),
                DnsRecord(name='test', type='TXT', content='mock entry 2'),
                DnsRecord(name='', type='AAAA', content='fe80::1'),
                DnsRecord(name='autoconfig', type='AAAA', content='fe80::1'),
                DnsRecord(name='git', type='AAAA', content='fe80::1'),
                DnsRecord(name='mail', type='AAAA', content='fe80::1'),
                DnsRecord(name='www', type='AAAA', content='fe80::1'),
            ]
        },
    )
    mock_execute_operations_plan.assert_not_called()


@pytest.mark.parametrize(
    "data",
    [
        "",
        "n",
        "N",
        "1",
    ],
)
def test_cli_abort(runner, monkeypatch, data):
    mock_api = Mock()
    monkeypatch.setattr(api, "PorkbunAPI", mock_api)
    mock_api().get_my_ip.return_value = "some-ip-address"

    mock_collect_existing_dns_records = Mock()
    monkeypatch.setattr(cli, '_collect_existing_dns_records', mock_collect_existing_dns_records)
    mock_collect_existing_dns_records.return_value = "existing-records"

    mock_plan_operations = Mock()
    monkeypatch.setattr(cli, '_plan_operations', mock_plan_operations)
    mock_plan_operations.return_value = "operations-plan"

    mock_execute_operations_plan = Mock()
    monkeypatch.setattr(cli, '_execute_operations_plan', mock_execute_operations_plan)

    result = runner.invoke(cli.main, ['tests/config.yml', '--mode', 'replace', '--verbose'], input=data)

    print(f"output : '{result.output.strip()}'")

    assert result.exit_code == 0
    assert not result.exception
    assert result.output.strip() == '\n'.join([
        "IP address reported by API 'some-ip-address'",
        "Would you like to proceed? [yN]: ",
        "Operation aborted.",
    ])

    # Assertions on calls
    mock_collect_existing_dns_records.assert_called_once_with(mock_api(), ["example.com"], 1)
    mock_plan_operations.assert_called_once_with(
        "replace",
        1,
        "existing-records",
        {
            'example.com': [
                DnsRecord(name='', type='A', content='192.168.192.168'),
                DnsRecord(name='autoconfig', type='A', content='192.168.192.168'),
                DnsRecord(name='git', type='A', content='192.168.192.168'),
                DnsRecord(name='mail', type='A', content='192.168.192.168'),
                DnsRecord(name='www', type='A', content='192.168.192.168'),
                DnsRecord(name='', type='MX', content='mail.example.com'),
                DnsRecord(name='', type='TXT', content='mock entry 1'),
                DnsRecord(name='test', type='TXT', content='mock entry 2'),
                DnsRecord(name='', type='AAAA', content='fe80::1'),
                DnsRecord(name='autoconfig', type='AAAA', content='fe80::1'),
                DnsRecord(name='git', type='AAAA', content='fe80::1'),
                DnsRecord(name='mail', type='AAAA', content='fe80::1'),
                DnsRecord(name='www', type='AAAA', content='fe80::1'),
            ]
        },
    )
    mock_execute_operations_plan.assert_not_called()


def test_cli(runner, monkeypatch):
    mock_api = Mock()
    monkeypatch.setattr(api, "PorkbunAPI", mock_api)
    mock_api().get_my_ip.return_value = "some-ip-address"

    mock_collect_existing_dns_records = Mock()
    monkeypatch.setattr(cli, '_collect_existing_dns_records', mock_collect_existing_dns_records)
    mock_collect_existing_dns_records.return_value = "existing-records"

    mock_plan_operations = Mock()
    monkeypatch.setattr(cli, '_plan_operations', mock_plan_operations)
    mock_plan_operations.return_value = "operations-plan"

    mock_execute_operations_plan = Mock()
    monkeypatch.setattr(cli, '_execute_operations_plan', mock_execute_operations_plan)

    result = runner.invoke(cli.main, ['tests/config.yml', '--mode', 'replace', '--verbose'], input='y')

    print(f"output : '{result.output.strip()}'")

    assert result.exit_code == 0
    assert not result.exception
    assert result.output.strip() == '\n'.join([
        "IP address reported by API 'some-ip-address'",
        "Would you like to proceed? [yN]:",
    ])

    # Assertions on calls
    mock_collect_existing_dns_records.assert_called_once_with(mock_api(), ["example.com"], 1)
    mock_plan_operations.assert_called_once_with(
        "replace",
        1,
        "existing-records",
        {
            'example.com': [
                DnsRecord(name='', type='A', content='192.168.192.168'),
                DnsRecord(name='autoconfig', type='A', content='192.168.192.168'),
                DnsRecord(name='git', type='A', content='192.168.192.168'),
                DnsRecord(name='mail', type='A', content='192.168.192.168'),
                DnsRecord(name='www', type='A', content='192.168.192.168'),
                DnsRecord(name='', type='MX', content='mail.example.com'),
                DnsRecord(name='', type='TXT', content='mock entry 1'),
                DnsRecord(name='test', type='TXT', content='mock entry 2'),
                DnsRecord(name='', type='AAAA', content='fe80::1'),
                DnsRecord(name='autoconfig', type='AAAA', content='fe80::1'),
                DnsRecord(name='git', type='AAAA', content='fe80::1'),
                DnsRecord(name='mail', type='AAAA', content='fe80::1'),
                DnsRecord(name='www', type='AAAA', content='fe80::1'),
            ]
        },
    )
    mock_execute_operations_plan.assert_called_once_with(mock_api(), 1, "operations-plan")


class TestHelpers(TestCase):
    @patch('porkbun_api_cli.cli._log_if_level')
    def test_collect_existing_dns_records(self, mock_log_if_level):
        mock_api = Mock()

        def list_dns_records_side_effect(domain_name):
            if domain_name == "fail.com":
                raise RuntimeError("API Error")
            return [ExistingDnsRecord(name="record1", type="A", content="", id="")]

        mock_api.list_dns_records.side_effect = list_dns_records_side_effect

        domain_names = ["pass.com", "fail.com"]
        verbose = 2
        result = cli._collect_existing_dns_records(mock_api, domain_names, verbose)

        # Assertions on result
        self.assertEqual(
            result,
            {"pass.com": [ExistingDnsRecord(name="record1", type="A", content="", id="")], "fail.com": None},
        )

        # Assertions on log calls
        expected_calls = [
            call(0, 2, "- querying records for 'pass.com' .. ", nl=False),
            call(0, 2, "done"),
            call(0, 2, "- querying records for 'fail.com' .. ", nl=False),
            call(0, 2, "failed"),
            call(0, 2, "Querying records for 'fail.com' failed: API Error", file=sys.stderr),
        ]

        self.assertListEqual(expected_calls, mock_log_if_level.mock_calls)

    @patch('porkbun_api_cli.cli._log_if_level')
    def test_plan_operations_replace_mode(self, mock_log_if_level):
        mode = "replace"
        verbose = 2
        existing_domains = {
            "replace.com": [
                ExistingDnsRecord(name="www.replace.com", type="A", id="r1", content="127.0.0.1", ttl=600),
                ExistingDnsRecord(name="autoconfig.replace.com", type="A", id="r2", content="127.0.0.1", ttl=3600),
                ExistingDnsRecord(name="mail.replace.com", type="MX", id="r3", content="mail.replace.com", ttl=3600),
            ],
            "new.com": [
                ExistingDnsRecord(name="www.new.com", type="A", id="n1", content="192.168.192.168", ttl=3600),
                ExistingDnsRecord(name="mail.new.com", type="MX", id="n2", content="mail.new.com", ttl=3600),
            ],
            "another.com": [
                ExistingDnsRecord(name="www.another.com", type="A", id="a1", content="10.0.0.1", ttl=3600),
                ExistingDnsRecord(name="mail.another.com", type="MX", id="a2", content="mail.another.com", ttl=3600),
            ],
            "fail.com": None,
        }
        config_domains = {
            "replace.com": [
                DnsRecord(name="www", type="A", content="127.0.0.1", ttl=3600),
                DnsRecord(name="autoconfig", type="A", content="127.0.0.1", ttl=3600),
                DnsRecord(name="ftp", type="A", content="127.0.0.1", ttl=3600),
            ],
            "new.com": [
                DnsRecord(name="www", type="A", content="169.254.169.254", ttl=3600),
                DnsRecord(name="mail", type="MX", content="new-mail.new.com", ttl=3600),
            ],
        }

        # Calling the function
        result = cli._plan_operations(mode, verbose, existing_domains, config_domains)

        # Assertions on result
        self.assertEqual(len(result), 4)  # Four domains processed
        self.assertIn("replace.com", result)
        self.assertEqual(len(result["replace.com"]), 4)
        self.assertEqual(result["replace.com"][0].operation, "update")
        self.assertEqual(result["replace.com"][0].new.name, "www")
        self.assertEqual(result["replace.com"][1].operation, "match")
        self.assertEqual(result["replace.com"][1].new.name, "autoconfig")
        self.assertEqual(result["replace.com"][1].existing.id, "r2")
        self.assertEqual(result["replace.com"][2].operation, "create")
        self.assertEqual(result["replace.com"][2].new.name, "ftp")
        self.assertEqual(result["replace.com"][3].operation, "delete")
        self.assertEqual(result["replace.com"][3].existing.name, "mail.replace.com")
        self.assertIn("new.com", result)
        self.assertEqual(len(result["new.com"]), 2)
        self.assertEqual(result["new.com"][0].operation, "update")
        self.assertEqual(result["new.com"][0].new.name, "www")
        self.assertEqual(result["new.com"][1].operation, "update")
        self.assertEqual(result["new.com"][1].new.name, "mail")
        self.assertIn("another.com", result)
        self.assertTrue(result["another.com"] is None)

        # Assertions on log calls
        expected_calls = [
            call(1, 2, "\n\tPROCESSING EXISTING RECORDS\n"),
            call(1, 2, "skipping 'another.com': not included in current configuration"),
            call(0, 2, "skipping 'fail.com': querying existing records failed"),
            call(2, 2, "\t- update A-record 'www.new.com'"),
            call(2, 2, "\t- update MX-record 'mail.new.com'"),
            call(2, 2, "\t- update A-record 'www.replace.com'"),
            call(3, 2, "\t- found matching A-record 'autoconfig.replace.com'"),
            call(2, 2, "\t- create A-record 'ftp.replace.com'"),
            call(2, 2, "\t- delete MX-record 'mail.replace.com'"),
        ]

        self.assertListEqual(expected_calls, mock_log_if_level.mock_calls)

    @patch('porkbun_api_cli.cli._log_if_level')
    def test_plan_operations_append_mode(self, mock_log_if_level):
        mode = "append"
        verbose = 2
        existing_domains = {
            "append.com": [
                ExistingDnsRecord(name="www.append.com", type="A", id="a1", content="127.0.0.1", ttl=3600),
                ExistingDnsRecord(name="mail.append.com", type="MX", id="a2", content="mail.append.com", ttl=3600),
            ],
            "another.com": [
                ExistingDnsRecord(name="www.another.com", type="A", id="a3", content="10.0.0.1", ttl=3600),
                ExistingDnsRecord(name="mail.another.com", type="MX", id="a4", content="mail.another.com", ttl=3600),
            ],
            "fail.com": None,
        }
        config_domains = {
            "append.com": [
                DnsRecord(name="www", type="A", content="127.0.0.1", ttl=600),
                DnsRecord(name="ftp", type="A", content="127.0.0.1", ttl=3600),
                DnsRecord(name="mail", type="MX", content="mail.append.com", ttl=3600),
            ]
        }

        # Calling the function
        result = cli._plan_operations(mode, verbose, existing_domains, config_domains)

        # Assertions on result
        self.assertEqual(len(result), 3)  # Three domains processed
        self.assertIn("append.com", result)
        self.assertEqual(len(result["append.com"]), 2)
        self.assertEqual(result["append.com"][0].operation, "create")
        self.assertEqual(result["append.com"][0].new.name, "ftp")
        self.assertEqual(result["append.com"][1].operation, "match")
        self.assertEqual(result["append.com"][1].new.name, "mail")
        self.assertEqual(result["append.com"][1].existing.id, "a2")
        self.assertIn("another.com", result)
        self.assertTrue(result["another.com"] is None)

        # Assertions on log calls
        expected_calls = [
            call(1, 2, "\n\tPROCESSING EXISTING RECORDS\n"),
            call(1, 2, "skipping 'another.com': not included in current configuration"),
            call(2, 2, "\t- create A-record 'ftp.append.com'"),
            call(3, 2, "\t- found matching MX-record 'mail.append.com'"),
            call(0, 2, "skipping 'fail.com': querying existing records failed"),
        ]

        self.assertListEqual(expected_calls, mock_log_if_level.mock_calls)

    @patch('porkbun_api_cli.cli._log_if_level')
    def test_plan_operations_update_mode(self, mock_log_if_level):
        mode = "update"
        verbose = 2
        existing_domains = {
            "update.com": [
                ExistingDnsRecord(name="www.update.com", type="A", id="u1", content="127.0.0.1", ttl=3600),
                ExistingDnsRecord(name="mail.update.com", type="MX", id="u2", content="mail.update.com", ttl=3600),
            ],
            "another.com": [
                ExistingDnsRecord(name="www.another.com", type="A", id="u3", content="10.0.0.1", ttl=3600),
                ExistingDnsRecord(name="mail.another.com", type="MX", id="u4", content="mail.another.com", ttl=3600),
            ],
            "fail.com": None,
        }
        config_domains = {
            "update.com": [
                DnsRecord(name="www", type="A", content="169.254.169.254", ttl=3600),
                DnsRecord(name="ftp", type="A", content="192.168.192.168", ttl=3600),
                DnsRecord(name="mail", type="MX", content="mail.update.com", ttl=3600),
            ]
        }

        # Calling the function
        result = cli._plan_operations(mode, verbose, existing_domains, config_domains)

        # Assertions on result
        self.assertEqual(len(result), 3)  # Three domains processed
        self.assertIn("update.com", result)
        self.assertEqual(len(result["update.com"]), 2)
        self.assertEqual(result["update.com"][0].operation, "update")
        self.assertEqual(result["update.com"][0].new.name, "www")
        self.assertEqual(result["update.com"][1].operation, "match")
        self.assertEqual(result["update.com"][1].new.name, "mail")
        self.assertEqual(result["update.com"][1].existing.id, "u2")
        self.assertIn("another.com", result)
        self.assertTrue(result["another.com"] is None)

        # Assertions on log calls
        expected_calls = [
            call(1, 2, "\n\tPROCESSING EXISTING RECORDS\n"),
            call(1, 2, "skipping 'another.com': not included in current configuration"),
            call(0, 2, "skipping 'fail.com': querying existing records failed"),
            call(2, 2, "\t- update A-record 'www.update.com'"),
            call(3, 2, "\t- found matching MX-record 'mail.update.com'"),
        ]

        self.assertListEqual(expected_calls, mock_log_if_level.mock_calls)

    @patch('porkbun_api_cli.cli._log_if_level')
    def test_plan_operations_upgrade_mode(self, mock_log_if_level):
        mode = "upgrade"
        verbose = 2
        existing_domains = {
            "upgrade.com": [
                ExistingDnsRecord(name="www.upgrade.com", type="A", id="u1", content="127.0.0.1", ttl=3600),
                ExistingDnsRecord(name="mail.upgrade.com", type="MX", id="u2", content="mail.upgrade.com", ttl=3600),
            ],
            "another.com": [
                ExistingDnsRecord(name="www.another.com", type="A", id="u3", content="10.0.0.1", ttl=3600),
                ExistingDnsRecord(name="mail.another.com", type="MX", id="u4", content="mail.another.com", ttl=3600),
            ],
            "fail.com": None,
        }
        config_domains = {
            "upgrade.com": [
                DnsRecord(name="www", type="A", content="169.254.169.254", ttl=3600),
                DnsRecord(name="ftp", type="A", content="192.168.192.168", ttl=3600),
                DnsRecord(name="mail", type="MX", content="mail.upgrade.com", ttl=3600),
            ]
        }

        # Calling the function
        result = cli._plan_operations(mode, verbose, existing_domains, config_domains)

        # Assertions on result
        self.assertEqual(len(result), 3)  # Three domains processed
        self.assertIn("upgrade.com", result)
        self.assertEqual(len(result["upgrade.com"]), 3)
        self.assertEqual(result["upgrade.com"][0].operation, "update")
        self.assertEqual(result["upgrade.com"][0].new.name, "www")
        self.assertEqual(result["upgrade.com"][1].operation, "create")
        self.assertEqual(result["upgrade.com"][1].new.name, "ftp")
        self.assertEqual(result["upgrade.com"][2].operation, "match")
        self.assertEqual(result["upgrade.com"][2].new.name, "mail")
        self.assertEqual(result["upgrade.com"][2].existing.id, "u2")
        self.assertIn("another.com", result)
        self.assertTrue(result["another.com"] is None)

        # Assertions on log calls
        expected_calls = [
            call(1, 2, "\n\tPROCESSING EXISTING RECORDS\n"),
            call(1, 2, "skipping 'another.com': not included in current configuration"),
            call(0, 2, "skipping 'fail.com': querying existing records failed"),
            call(2, 2, "\t- update A-record 'www.upgrade.com'"),
            call(2, 2, "\t- create A-record 'ftp.upgrade.com'"),
            call(3, 2, "\t- found matching MX-record 'mail.upgrade.com'"),
        ]

        self.assertListEqual(expected_calls, mock_log_if_level.mock_calls)

    @patch('porkbun_api_cli.cli._log_if_level')
    def test_plan_operations_emits_exactly_one_match_entry(self, mock_log_if_level):
        mode = "replace"
        verbose = 3
        existing_domains = {
            "match.com": [
                ExistingDnsRecord(name="www.match.com", type="A", id="m1", content="127.0.0.1", ttl=600),
            ],
            "fail.com": None,
        }
        config_domains = {
            "match.com": [
                DnsRecord(name="www", type="A", content="127.0.0.1", ttl=600),
            ],
        }

        result = cli._plan_operations(mode, verbose, existing_domains, config_domains)

        self.assertEqual(len(result["match.com"]), 1)
        self.assertIsInstance(result["match.com"][0], PlanEntry)
        self.assertEqual(result["match.com"][0].operation, "match")
        self.assertEqual(result["match.com"][0].new.name, "www")
        self.assertEqual(result["match.com"][0].existing.id, "m1")
        expected_calls = [
            call(1, 3, "\n\tPROCESSING EXISTING RECORDS\n"),
            call(0, 3, "skipping 'fail.com': querying existing records failed"),
            call(3, 3, "\t- found matching A-record 'www.match.com'"),
        ]
        self.assertListEqual(expected_calls, mock_log_if_level.mock_calls)

    @patch('porkbun_api_cli.cli._log_if_level')
    def test_plan_operations_ttl_zero_emits_warning(self, mock_log_if_level):
        mode = "append"
        verbose = 2
        existing_domains = {
            "ttl.com": [
                ExistingDnsRecord(name="www.ttl.com", type="A", id="1", content="127.0.0.1", ttl=600),
            ],
            "fail.com": None,
        }
        config_domains = {
            "ttl.com": [
                DnsRecord(name="www", type="A", content="127.0.0.1", ttl=0),
            ],
        }

        result = cli._plan_operations(mode, verbose, existing_domains, config_domains)

        self.assertEqual(len(result), 2)
        self.assertEqual(len(result["ttl.com"]), 1)
        self.assertEqual(result["ttl.com"][0].operation, "match")
        self.assertEqual(result["ttl.com"][0].new.name, "www")
        expected_calls = [
            call(1, 2, "\n\tPROCESSING EXISTING RECORDS\n"),
            call(0, 2, "skipping 'fail.com': querying existing records failed"),
            call(
                0,
                2,
                "ttl=0 in config treated as 'use default'; ttl comparison skipped for www.ttl.com",
                file=sys.stderr,
            ),
            call(3, 2, "\t- found matching A-record 'www.ttl.com'"),
        ]
        self.assertListEqual(expected_calls, mock_log_if_level.mock_calls)

    @patch('porkbun_api_cli.cli._log_if_level')
    def test_plan_operations_prio_omitted_emits_warning(self, mock_log_if_level):
        mode = "append"
        verbose = 2
        existing_domains = {
            "prio.com": [
                ExistingDnsRecord(name="mail.prio.com", type="MX", id="1", content="mail.prio.com", ttl=600, prio=10),
            ],
            "fail.com": None,
        }
        config_domains = {
            "prio.com": [
                DnsRecord(name="mail", type="MX", content="mail.prio.com", ttl=600),
            ],
        }

        result = cli._plan_operations(mode, verbose, existing_domains, config_domains)

        self.assertEqual(len(result), 2)
        self.assertEqual(len(result["prio.com"]), 1)
        self.assertEqual(result["prio.com"][0].operation, "match")
        self.assertEqual(result["prio.com"][0].new.name, "mail")
        expected_calls = [
            call(1, 2, "\n\tPROCESSING EXISTING RECORDS\n"),
            call(0, 2, "skipping 'fail.com': querying existing records failed"),
            call(
                0,
                2,
                "prio omitted in config; server returned prio=10 for mail.prio.com",
                file=sys.stderr,
            ),
            call(3, 2, "\t- found matching MX-record 'mail.prio.com'"),
        ]
        self.assertListEqual(expected_calls, mock_log_if_level.mock_calls)

    @patch('porkbun_api_cli.cli._log_if_level')
    def test_execute_operations_plan(self, mock_log_if_level):
        # Mocking API and input arguments
        mock_api = Mock()
        verbose = 2
        operations_plan = {
            "pass.com": [
                Operation(operation="create", new=DnsRecord(name="", type="A", content="")),
                Operation(operation="create", new=DnsRecord(name="www", type="A", content="")),
                Operation(
                    operation="update",
                    existing=ExistingDnsRecord(name="www.pass.com", type="A", id="123", content=""),
                    new=DnsRecord(name="www", type="A", content=""),
                ),
                Operation(
                    operation="delete",
                    existing=ExistingDnsRecord(name="mail.pass.com", type="MX", id="456", content=""),
                ),
            ],
            "fail.com": [
                Operation(operation="create", new=DnsRecord(name="www", type="A", content="")),
                Operation(
                    operation="update",
                    existing=ExistingDnsRecord(name="www.fail.com", type="A", id="321", content=""),
                    new=DnsRecord(name="www", type="A", content=""),
                ),
                Operation(
                    operation="delete",
                    existing=ExistingDnsRecord(name="mail.fail.com", type="MX", id="654", content=""),
                ),
            ],
            "invalid.com": [
                Operation(operation="invalid"),
            ],
        }

        # Mocking API to raise exception during operation execution
        def create_record_side_effect(domain_name, record):
            if domain_name == "fail.com":
                raise RuntimeError("create_record error")
            else:
                return

        mock_api.create_record.side_effect = create_record_side_effect

        def update_record_side_effect(domain_name, existing_id, new_record):
            if domain_name == "fail.com":
                raise RuntimeError("update_record error")
            else:
                return

        mock_api.update_record.side_effect = update_record_side_effect

        # Calling the function
        cli._execute_operations_plan(mock_api, verbose, operations_plan)

        # Assertions on log calls
        expected_calls = [
            call(1, 2, '\n\tEXECUTION\n'),
            call(1, 2, "- altering domain 'pass.com'"),
            call(1, 2, "\tcreate A-record 'pass.com' ... ", nl=False),
            call(1, 2, 'done'),
            call(1, 2, "\tcreate A-record 'www.pass.com' ... ", nl=False),
            call(1, 2, 'done'),
            call(1, 2, "\tupdate A-record 'www.pass.com' ... ", nl=False),
            call(1, 2, 'done'),
            call(1, 2, "\tdelete MX-record 'mail.pass.com' ... ", nl=False),
            call(0, 2, 'delete operation is not implemented - skipped'),
            call(1, 2, "- altering domain 'fail.com'"),
            call(1, 2, "\tcreate A-record 'www.fail.com' ... ", nl=False),
            call(0, 2, "querying Porkbun API for domain 'fail.com' failed: create_record error"),
            call(1, 2, "\tupdate A-record 'www.fail.com' ... ", nl=False),
            call(0, 2, "querying Porkbun API for domain 'fail.com' failed: update_record error"),
            call(1, 2, "\tdelete MX-record 'mail.fail.com' ... ", nl=False),
            call(0, 2, 'delete operation is not implemented - skipped'),
            call(1, 2, "- altering domain 'invalid.com'"),
            call(0, 2, "unknown operation 'invalid'"),
        ]

        self.assertListEqual(expected_calls, mock_log_if_level.mock_calls)
