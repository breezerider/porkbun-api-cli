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
    assert result.output.strip() == '\n'.join(
        [
            "dry run requested, enable verbose output",
            "IP address reported by API 'some-ip-address'",
            "dry run requested, skipping execution",
        ]
    )

    # Assertions on calls
    mock_collect_existing_dns_records.assert_called_once_with(mock_api(), ["example.com"], 2)
    mock_plan_operations.assert_called_once_with(
        "append",
        2,
        "existing-records",
        {
            'example.com': [
                {'name': '', 'type': 'A', 'content': '192.168.192.168'},
                {'name': 'autoconfig', 'type': 'A', 'content': '192.168.192.168'},
                {'name': 'git', 'type': 'A', 'content': '192.168.192.168'},
                {'name': 'mail', 'type': 'A', 'content': '192.168.192.168'},
                {'name': 'www', 'type': 'A', 'content': '192.168.192.168'},
                {'name': '', 'type': 'MX', 'content': 'mail.example.com'},
                {'name': '', 'type': 'TXT', 'content': 'mock entry 1'},
                {'name': 'test', 'type': 'TXT', 'content': 'mock entry 2'},
                {'name': '', 'type': 'AAAA', 'content': 'fe80::1'},
                {'name': 'autoconfig', 'type': 'AAAA', 'content': 'fe80::1'},
                {'name': 'git', 'type': 'AAAA', 'content': 'fe80::1'},
                {'name': 'mail', 'type': 'AAAA', 'content': 'fe80::1'},
                {'name': 'www', 'type': 'AAAA', 'content': 'fe80::1'},
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
    assert result.output.strip() == '\n'.join(
        ["IP address reported by API 'some-ip-address'", "Would you like to proceed? [yN]: ", "Operation aborted."]
    )

    # Assertions on calls
    mock_collect_existing_dns_records.assert_called_once_with(mock_api(), ["example.com"], 1)
    mock_plan_operations.assert_called_once_with(
        "replace",
        1,
        "existing-records",
        {
            'example.com': [
                {'name': '', 'type': 'A', 'content': '192.168.192.168'},
                {'name': 'autoconfig', 'type': 'A', 'content': '192.168.192.168'},
                {'name': 'git', 'type': 'A', 'content': '192.168.192.168'},
                {'name': 'mail', 'type': 'A', 'content': '192.168.192.168'},
                {'name': 'www', 'type': 'A', 'content': '192.168.192.168'},
                {'name': '', 'type': 'MX', 'content': 'mail.example.com'},
                {'name': '', 'type': 'TXT', 'content': 'mock entry 1'},
                {'name': 'test', 'type': 'TXT', 'content': 'mock entry 2'},
                {'name': '', 'type': 'AAAA', 'content': 'fe80::1'},
                {'name': 'autoconfig', 'type': 'AAAA', 'content': 'fe80::1'},
                {'name': 'git', 'type': 'AAAA', 'content': 'fe80::1'},
                {'name': 'mail', 'type': 'AAAA', 'content': 'fe80::1'},
                {'name': 'www', 'type': 'AAAA', 'content': 'fe80::1'},
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
    assert result.output.strip() == '\n'.join(
        ["IP address reported by API 'some-ip-address'", "Would you like to proceed? [yN]:"]
    )

    # Assertions on calls
    mock_collect_existing_dns_records.assert_called_once_with(mock_api(), ["example.com"], 1)
    mock_plan_operations.assert_called_once_with(
        "replace",
        1,
        "existing-records",
        {
            'example.com': [
                {'name': '', 'type': 'A', 'content': '192.168.192.168'},
                {'name': 'autoconfig', 'type': 'A', 'content': '192.168.192.168'},
                {'name': 'git', 'type': 'A', 'content': '192.168.192.168'},
                {'name': 'mail', 'type': 'A', 'content': '192.168.192.168'},
                {'name': 'www', 'type': 'A', 'content': '192.168.192.168'},
                {'name': '', 'type': 'MX', 'content': 'mail.example.com'},
                {'name': '', 'type': 'TXT', 'content': 'mock entry 1'},
                {'name': 'test', 'type': 'TXT', 'content': 'mock entry 2'},
                {'name': '', 'type': 'AAAA', 'content': 'fe80::1'},
                {'name': 'autoconfig', 'type': 'AAAA', 'content': 'fe80::1'},
                {'name': 'git', 'type': 'AAAA', 'content': 'fe80::1'},
                {'name': 'mail', 'type': 'AAAA', 'content': 'fe80::1'},
                {'name': 'www', 'type': 'AAAA', 'content': 'fe80::1'},
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
            return {"record1": "value1", "record2": "value2"}

        mock_api.list_dns_records.side_effect = list_dns_records_side_effect

        domain_names = ["pass.com", "fail.com"]
        verbose = 2
        result = cli._collect_existing_dns_records(mock_api, domain_names, verbose)

        # Assertions on result
        self.assertEqual(result, {"pass.com": {"record1": "value1", "record2": "value2"}, "fail.com": None})

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
                {"name": "www.replace.com", "type": "A", "content": "127.0.0.1", "ttl": 600},
                {"name": "autoconfig.replace.com", "type": "A", "content": "127.0.0.1", "ttl": 3600},
                {"name": "mail.replace.com", "type": "MX", "content": "mail.replace.com", "ttl": 3600},
            ],
            "new.com": [
                {"name": "www.new.com", "type": "A", "content": "192.168.192.168", "ttl": 3600},
                {"name": "mail.new.com", "type": "MX", "content": "mail.new.com", "ttl": 3600},
            ],
            "another.com": [
                {"name": "www.another.com", "type": "A", "content": "10.0.0.1", "ttl": 3600},
                {"name": "mail.another.com", "type": "MX", "content": "mail.another.com", "ttl": 3600},
            ],
            "fail.com": None,
        }
        config_domains = {
            "replace.com": [
                {"name": "www", "type": "A", "content": "127.0.0.1", "ttl": 3600},
                {"name": "autoconfig", "type": "A", "content": "127.0.0.1", "ttl": 3600},
                {"name": "ftp", "type": "A", "content": "127.0.0.1", "ttl": 3600},
            ],
            "new.com": [
                {"name": "www", "type": "A", "content": "169.254.169.254", "ttl": 3600},
                {"name": "mail", "type": "MX", "content": "new-mail.new.com", "ttl": 3600},
            ],
        }

        # Calling the function
        result = cli._plan_operations(mode, verbose, existing_domains, config_domains)

        # Assertions on result
        self.assertEqual(len(result), 4)  # Four domains processed
        self.assertIn("replace.com", result)
        self.assertEqual(len(result["replace.com"]), 3)
        self.assertEqual(result["replace.com"][0]["operation"], "update")
        self.assertEqual(result["replace.com"][0]["new"]["name"], "www")
        self.assertEqual(result["replace.com"][1]["operation"], "create")
        self.assertEqual(result["replace.com"][1]["new"]["name"], "ftp")
        self.assertEqual(result["replace.com"][2]["operation"], "delete")
        self.assertEqual(result["replace.com"][2]["existing"]["name"], "mail.replace.com")
        self.assertIn("new.com", result)
        self.assertEqual(len(result["new.com"]), 2)
        self.assertEqual(result["new.com"][0]["operation"], "update")
        self.assertEqual(result["new.com"][0]["new"]["name"], "www")
        self.assertEqual(result["new.com"][1]["operation"], "update")
        self.assertEqual(result["new.com"][1]["new"]["name"], "mail")
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
                {"name": "www.append.com", "type": "A", "content": "127.0.0.1", "ttl": 3600},
                {"name": "mail.append.com", "type": "MX", "content": "mail.append.com", "ttl": 3600},
            ],
            "another.com": [
                {"name": "www.another.com", "type": "A", "content": "10.0.0.1", "ttl": 3600},
                {"name": "mail.another.com", "type": "MX", "content": "mail.another.com", "ttl": 3600},
            ],
            "fail.com": None,
        }
        config_domains = {
            "append.com": [
                {"name": "www", "type": "A", "content": "127.0.0.1", "ttl": 600},
                {"name": "ftp", "type": "A", "content": "127.0.0.1", "ttl": 3600},
                {"name": "mail", "type": "MX", "content": "mail.append.com", "ttl": 3600},
            ]
        }

        # Calling the function
        result = cli._plan_operations(mode, verbose, existing_domains, config_domains)

        # Assertions on result
        self.assertEqual(len(result), 3)  # Three domains processed
        self.assertIn("append.com", result)
        self.assertEqual(len(result["append.com"]), 1)
        self.assertEqual(result["append.com"][0]["operation"], "create")
        self.assertEqual(result["append.com"][0]["new"]["name"], "ftp")
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
                {"name": "www.update.com", "type": "A", "content": "127.0.0.1", "ttl": 3600},
                {"name": "mail.update.com", "type": "MX", "content": "mail.update.com", "ttl": 3600},
            ],
            "another.com": [
                {"name": "www.another.com", "type": "A", "content": "10.0.0.1", "ttl": 3600},
                {"name": "mail.another.com", "type": "MX", "content": "mail.another.com", "ttl": 3600},
            ],
            "fail.com": None,
        }
        config_domains = {
            "update.com": [
                {"name": "www", "type": "A", "content": "169.254.169.254", "ttl": 3600},
                {"name": "ftp", "type": "A", "content": "192.168.192.168", "ttl": 3600},
                {"name": "mail", "type": "MX", "content": "mail.update.com", "ttl": 3600},
            ]
        }

        # Calling the function
        result = cli._plan_operations(mode, verbose, existing_domains, config_domains)

        # Assertions on result
        self.assertEqual(len(result), 3)  # Three domains processed
        self.assertIn("update.com", result)
        self.assertEqual(len(result["update.com"]), 1)
        self.assertEqual(result["update.com"][0]["operation"], "update")
        self.assertEqual(result["update.com"][0]["new"]["name"], "www")
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
                {"name": "www.upgrade.com", "type": "A", "content": "127.0.0.1", "ttl": 3600},
                {"name": "mail.upgrade.com", "type": "MX", "content": "mail.upgrade.com", "ttl": 3600},
            ],
            "another.com": [
                {"name": "www.another.com", "type": "A", "content": "10.0.0.1", "ttl": 3600},
                {"name": "mail.another.com", "type": "MX", "content": "mail.another.com", "ttl": 3600},
            ],
            "fail.com": None,
        }
        config_domains = {
            "upgrade.com": [
                {"name": "www", "type": "A", "content": "169.254.169.254", "ttl": 3600},
                {"name": "ftp", "type": "A", "content": "192.168.192.168", "ttl": 3600},
                {"name": "mail", "type": "MX", "content": "mail.upgrade.com", "ttl": 3600},
            ]
        }

        # Calling the function
        result = cli._plan_operations(mode, verbose, existing_domains, config_domains)

        # Assertions on result
        self.assertEqual(len(result), 3)  # Three domains processed
        self.assertIn("upgrade.com", result)
        self.assertEqual(len(result["upgrade.com"]), 2)
        self.assertEqual(result["upgrade.com"][0]["operation"], "update")
        self.assertEqual(result["upgrade.com"][0]["new"]["name"], "www")
        self.assertEqual(result["upgrade.com"][1]["operation"], "create")
        self.assertEqual(result["upgrade.com"][1]["new"]["name"], "ftp")
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
    def test_execute_operations_plan(self, mock_log_if_level):
        # Mocking API and input arguments
        mock_api = Mock()
        verbose = 2
        operations_plan = {
            "pass.com": [
                {"operation": "create", "new": {"name": "", "type": "A"}},
                {"operation": "create", "new": {"name": "www", "type": "A"}},
                {
                    "operation": "update",
                    "existing": {"id": "123", "name": "www", "type": "A"},
                    "new": {"name": "www", "type": "A"},
                },
                {"operation": "delete", "existing": {"id": "456", "name": "mail.pass.com", "type": "MX"}},
            ],
            "fail.com": [
                {"operation": "create", "new": {"name": "www", "type": "A"}},
                {
                    "operation": "update",
                    "existing": {"id": "321", "name": "www", "type": "A"},
                    "new": {"name": "www", "type": "A"},
                },
                {"operation": "delete", "existing": {"id": "654", "name": "mail.fail.com", "type": "MX"}},
            ],
            "invalid.com": [
                {"operation": "invalid"},
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
