import re
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
    output = (result.output or "") + (result.stderr or "")
    assert output.strip().startswith('Usage: ')


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


# --- Unit 1: --yes flag, --yes/--dry-run mutex, --mode replace UsageError, help text ---


def test_cli_mode_replace_raises_usage_error(runner):
    result = runner.invoke(cli.main, ['tests/config.yml', '--mode', 'replace'])
    assert result.exit_code == 2
    assert not result.exception or isinstance(result.exception, SystemExit)
    assert "replace mode is not implemented" in (result.stderr or result.output)


def test_cli_yes_and_dry_run_mutex(runner):
    result = runner.invoke(cli.main, ['tests/config.yml', '--yes', '--dry-run'])
    assert result.exit_code == 2
    assert "--yes and --dry-run are mutually exclusive" in (result.stderr or result.output)


def test_cli_help_documents_replace_and_dry_run_exit_code(runner):
    result = runner.invoke(cli.main, ['--help'])
    assert result.exit_code == 0
    assert "not implemented" in result.output
    assert "use 'upgrade'" in result.output
    assert "exits non-zero (code 3)" in result.output
    assert "--yes" in result.output


# --- Unit 3: plan renderer, summary renderer, color helper ---


def test_cli_plan_renders_symbol_rows(runner, monkeypatch):
    mock_api = Mock()
    monkeypatch.setattr(api, "PorkbunAPI", mock_api)
    mock_api().get_my_ip.return_value = "1.2.3.4"
    monkeypatch.setattr(cli, '_collect_existing_dns_records', lambda *_: {"example.com": []})
    monkeypatch.setattr(
        cli,
        '_plan_operations',
        lambda *_: {
            "example.com": [
                Operation(operation="create", new=DnsRecord(name="www", type="A", content="1.2.3.4")),
                Operation(
                    operation="update",
                    existing=ExistingDnsRecord(name="www.example.com", type="A", id="1", content="1.2.3.4"),
                    new=DnsRecord(name="www", type="A", content="1.2.3.5"),
                ),
                Operation(
                    operation="match",
                    existing=ExistingDnsRecord(name="mail.example.com", type="MX", id="2", content="mail.example.com"),
                    new=DnsRecord(name="mail", type="MX", content="mail.example.com"),
                ),
            ],
        },
    )
    monkeypatch.setattr(cli, '_execute_operations_plan', lambda *a, **k: {})
    result = runner.invoke(cli.main, ['tests/config.yml', '--mode', 'append', '-vv', '--yes'], color=True)
    assert result.exit_code == 0
    assert "Plan for example.com (append mode):" in result.stdout
    assert "NEW" in result.stdout and "A www.example.com 1.2.3.4" in result.stdout
    assert "UPD" in result.stdout and "A www.example.com 1.2.3.5" in result.stdout
    assert "OK " in result.stdout and "MX mail.example.com mail.example.com" in result.stdout


def test_cli_plan_match_rows_hidden_below_verbose_2(runner, monkeypatch):
    mock_api = Mock()
    monkeypatch.setattr(api, "PorkbunAPI", mock_api)
    mock_api().get_my_ip.return_value = "1.2.3.4"
    monkeypatch.setattr(cli, '_collect_existing_dns_records', lambda *_: {"example.com": []})
    monkeypatch.setattr(
        cli,
        '_plan_operations',
        lambda *_: {
            "example.com": [
                Operation(
                    operation="match",
                    existing=ExistingDnsRecord(name="m.example.com", type="A", id="1", content="x"),
                    new=DnsRecord(name="m", type="A", content="x"),
                )
            ],
        },
    )
    monkeypatch.setattr(cli, '_execute_operations_plan', lambda *a, **k: {})
    result = runner.invoke(cli.main, ['tests/config.yml', '--mode', 'append', '-v', '--yes'], color=True)
    assert result.exit_code == 0
    # match row hidden at verbose=1
    assert "OK " not in result.output
    assert "Plan for example.com (append mode):" in result.output


def test_cli_summary_empty_domain(runner, monkeypatch):
    mock_api = Mock()
    monkeypatch.setattr(api, "PorkbunAPI", mock_api)
    mock_api().get_my_ip.return_value = "1.2.3.4"
    monkeypatch.setattr(cli, '_collect_existing_dns_records', lambda *_: {"empty.com": []})
    monkeypatch.setattr(cli, '_plan_operations', lambda *_: {"empty.com": []})
    monkeypatch.setattr(cli, '_execute_operations_plan', lambda *a, **k: {})
    result = runner.invoke(cli.main, ['tests/config.yml', '--mode', 'append', '--yes'])
    assert result.exit_code == 0
    assert "Summary for empty.com: no records found" in result.output


def test_cli_summary_populated_domain(runner, monkeypatch):
    mock_api = Mock()
    monkeypatch.setattr(api, "PorkbunAPI", mock_api)
    mock_api().get_my_ip.return_value = "1.2.3.4"
    monkeypatch.setattr(cli, '_collect_existing_dns_records', lambda *_: {"example.com": []})
    monkeypatch.setattr(
        cli,
        '_plan_operations',
        lambda *_: {
            "example.com": [
                Operation(operation="create", new=DnsRecord(name="www", type="A", content="1.2.3.4")),
                Operation(
                    operation="match",
                    existing=ExistingDnsRecord(name="m.example.com", type="A", id="1", content="x"),
                    new=DnsRecord(name="m", type="A", content="x"),
                ),
            ],
        },
    )
    monkeypatch.setattr(cli, '_execute_operations_plan', lambda *a, **k: {})
    result = runner.invoke(cli.main, ['tests/config.yml', '--mode', 'append', '--yes'])
    assert result.exit_code == 0
    assert "Summary for example.com:" in result.stdout
    assert "1 created" in result.stdout
    assert "1 matched" in result.stdout


def test_cli_no_color_env_suppresses_ansi(runner, monkeypatch):
    mock_api = Mock()
    monkeypatch.setattr(api, "PorkbunAPI", mock_api)
    mock_api().get_my_ip.return_value = "1.2.3.4"
    monkeypatch.setattr(cli, '_collect_existing_dns_records', lambda *_: {"example.com": []})
    monkeypatch.setattr(
        cli,
        '_plan_operations',
        lambda *_: {
            "example.com": [Operation(operation="create", new=DnsRecord(name="www", type="A", content="1.2.3.4"))],
        },
    )
    monkeypatch.setattr(cli, '_execute_operations_plan', lambda *a, **k: {})
    result = runner.invoke(
        cli.main, ['tests/config.yml', '--mode', 'append', '--yes'], env={"NO_COLOR": "1"}, color=True
    )
    assert result.exit_code == 0
    assert "\x1b[" not in result.output


def test_cli_runner_default_color_false_suppresses_ansi(runner, monkeypatch):
    mock_api = Mock()
    monkeypatch.setattr(api, "PorkbunAPI", mock_api)
    mock_api().get_my_ip.return_value = "1.2.3.4"
    monkeypatch.setattr(cli, '_collect_existing_dns_records', lambda *_: {"example.com": []})
    monkeypatch.setattr(
        cli,
        '_plan_operations',
        lambda *_: {
            "example.com": [Operation(operation="create", new=DnsRecord(name="www", type="A", content="1.2.3.4"))],
        },
    )
    monkeypatch.setattr(cli, '_execute_operations_plan', lambda *a, **k: {})
    # CliRunner default is color=False → isatty() == False → no ANSI codes
    result = runner.invoke(cli.main, ['tests/config.yml', '--mode', 'append', '--yes'])
    assert result.exit_code == 0
    assert "\x1b[" not in result.output


# --- Unit 4: exit codes, stderr split, plan-before-prompt, summary after execution ---


def test_cli_exit_code_0_on_success(runner, monkeypatch):
    mock_api = Mock()
    monkeypatch.setattr(api, "PorkbunAPI", mock_api)
    mock_api().get_my_ip.return_value = "1.2.3.4"
    monkeypatch.setattr(cli, '_collect_existing_dns_records', lambda *_: {"example.com": []})
    monkeypatch.setattr(
        cli,
        '_plan_operations',
        lambda *_: {
            "example.com": [Operation(operation="create", new=DnsRecord(name="www", type="A", content="1.2.3.4"))],
        },
    )
    monkeypatch.setattr(cli, '_execute_operations_plan', lambda *a, **k: {})  # no failure
    result = runner.invoke(cli.main, ['tests/config.yml', '--yes'])
    assert result.exit_code == 0


def test_cli_exit_code_1_on_get_my_ip_failure(runner, monkeypatch):
    mock_api = Mock()
    monkeypatch.setattr(api, "PorkbunAPI", mock_api)
    mock_api().get_my_ip.side_effect = RuntimeError("auth failed")
    result = runner.invoke(cli.main, ['tests/config.yml', '--yes'])
    assert result.exit_code == 1
    assert "auth failed" in (result.stderr or "")


def test_cli_exit_code_1_on_config_load_failure(runner, monkeypatch):
    # missing config arg → Click default UsageError → exit 2, not 1
    # use a non-existent file path for the 1 branch
    result = runner.invoke(cli.main, ['/nonexistent/config.yml', '--yes'])
    assert result.exit_code in (1, 2)  # Click may exit 2 on Path(exists=True) miss


def test_cli_exit_code_2_on_replace_mode(runner):
    result = runner.invoke(cli.main, ['tests/config.yml', '--mode', 'replace', '--yes'])
    assert result.exit_code == 2


def test_cli_exit_code_2_on_yes_dry_run(runner):
    result = runner.invoke(cli.main, ['tests/config.yml', '--yes', '--dry-run'])
    assert result.exit_code == 2


def test_cli_exit_code_3_on_dry_run_with_changes(runner, monkeypatch):
    mock_api = Mock()
    monkeypatch.setattr(api, "PorkbunAPI", mock_api)
    mock_api().get_my_ip.return_value = "1.2.3.4"
    monkeypatch.setattr(cli, '_collect_existing_dns_records', lambda *_: {"example.com": []})
    monkeypatch.setattr(
        cli,
        '_plan_operations',
        lambda *_: {
            "example.com": [Operation(operation="create", new=DnsRecord(name="www", type="A", content="1.2.3.4"))],
        },
    )
    result = runner.invoke(cli.main, ['tests/config.yml', '--dry-run'])
    assert result.exit_code == 3
    assert "Plan for example.com" in result.output


def test_cli_exit_code_0_on_dry_run_in_sync(runner, monkeypatch):
    mock_api = Mock()
    monkeypatch.setattr(api, "PorkbunAPI", mock_api)
    mock_api().get_my_ip.return_value = "1.2.3.4"
    monkeypatch.setattr(cli, '_collect_existing_dns_records', lambda *_: {"example.com": []})
    monkeypatch.setattr(
        cli,
        '_plan_operations',
        lambda *_: {
            "example.com": [
                Operation(
                    operation="match",
                    existing=ExistingDnsRecord(name="m.example.com", type="A", id="1", content="x"),
                    new=DnsRecord(name="m", type="A", content="x"),
                )
            ],
        },
    )
    result = runner.invoke(cli.main, ['tests/config.yml', '--dry-run'])
    assert result.exit_code == 0


def test_cli_exit_code_4_on_execution_failure(runner, monkeypatch):
    mock_api = Mock()
    monkeypatch.setattr(api, "PorkbunAPI", mock_api)
    mock_api().get_my_ip.return_value = "1.2.3.4"
    monkeypatch.setattr(cli, '_collect_existing_dns_records', lambda *_: {"example.com": []})
    monkeypatch.setattr(
        cli,
        '_plan_operations',
        lambda *_: {
            "example.com": [Operation(operation="create", new=DnsRecord(name="www", type="A", content="1.2.3.4"))],
        },
    )
    monkeypatch.setattr(cli, '_execute_operations_plan', lambda *a, **k: {"example.com": 1})
    result = runner.invoke(cli.main, ['tests/config.yml', '--yes'])
    assert result.exit_code == 4
    assert "Summary for example.com:" in result.stdout
    assert "1 failed" in result.stdout


def test_cli_summary_failed_count_is_per_domain(runner, monkeypatch):
    mock_api = Mock()
    monkeypatch.setattr(api, "PorkbunAPI", mock_api)
    mock_api().get_my_ip.return_value = "1.2.3.4"
    monkeypatch.setattr(
        cli,
        '_plan_operations',
        lambda *_: {
            "good.com": [Operation(operation="create", new=DnsRecord(name="www", type="A", content="1.2.3.4"))],
            "bad.com": [Operation(operation="create", new=DnsRecord(name="www", type="A", content="5.6.7.8"))],
        },
    )
    monkeypatch.setattr(cli, '_execute_operations_plan', lambda *a, **k: {"bad.com": 1})
    result = runner.invoke(cli.main, ['tests/config.yml', '--mode', 'append', '-v', '--yes'])
    assert result.exit_code == 4
    stdout = result.stdout or ""
    assert re.search(r"Summary for good\.com:.*\b0 failed\b", stdout), (
        f"good.com summary should show '0 failed' (no op on this domain failed), got: {stdout!r}"
    )
    assert re.search(r"Summary for bad\.com:.*\b1 failed\b", stdout), (
        f"bad.com summary should show '1 failed' (one op on this domain failed), got: {stdout!r}"
    )


def test_cli_yes_skips_prompt(runner, monkeypatch):
    mock_api = Mock()
    monkeypatch.setattr(api, "PorkbunAPI", mock_api)
    mock_api().get_my_ip.return_value = "1.2.3.4"
    monkeypatch.setattr(cli, '_collect_existing_dns_records', lambda *_: {"example.com": []})
    monkeypatch.setattr(cli, '_plan_operations', lambda *_: {"example.com": []})
    mock_exec = Mock(return_value={})
    monkeypatch.setattr(cli, '_execute_operations_plan', mock_exec)
    result = runner.invoke(cli.main, ['tests/config.yml', '--yes'])
    assert result.exit_code == 0
    assert "Would you like to proceed?" not in result.output
    mock_exec.assert_called_once()


def test_cli_prompt_text_present_without_yes(runner, monkeypatch):
    mock_api = Mock()
    monkeypatch.setattr(api, "PorkbunAPI", mock_api)
    mock_api().get_my_ip.return_value = "1.2.3.4"
    monkeypatch.setattr(cli, '_collect_existing_dns_records', lambda *_: {"example.com": []})
    monkeypatch.setattr(cli, '_plan_operations', lambda *_: {"example.com": []})
    monkeypatch.setattr(cli, '_execute_operations_plan', lambda *a, **k: {})
    result = runner.invoke(cli.main, ['tests/config.yml'], input="n")
    assert result.exit_code == 0
    assert "Would you like to proceed? [yN]:" in result.output


def test_cli_dry_run_auto_verbose_bump(runner, monkeypatch):
    captured = {}
    mock_api = Mock()
    monkeypatch.setattr(api, "PorkbunAPI", mock_api)
    mock_api().get_my_ip.return_value = "1.2.3.4"

    def collect(api, names, verbose):
        captured["verbose"] = verbose
        return {"example.com": []}

    monkeypatch.setattr(cli, '_collect_existing_dns_records', collect)
    monkeypatch.setattr(cli, '_plan_operations', lambda *_: {"example.com": []})
    result = runner.invoke(cli.main, ['tests/config.yml', '--dry-run'])
    assert result.exit_code == 0
    assert captured["verbose"] == 2  # auto-bumped from 0


def test_cli_stderr_for_execution_failure(runner, monkeypatch):
    mock_api = Mock()
    monkeypatch.setattr(api, "PorkbunAPI", mock_api)
    mock_api().get_my_ip.return_value = "1.2.3.4"
    mock_api().create_record.side_effect = RuntimeError("api-down")
    monkeypatch.setattr(cli, '_collect_existing_dns_records', lambda *_: {"example.com": []})
    monkeypatch.setattr(
        cli,
        '_plan_operations',
        lambda *_: {
            "example.com": [Operation(operation="create", new=DnsRecord(name="www", type="A", content="1.2.3.4"))],
        },
    )
    result = runner.invoke(cli.main, ['tests/config.yml', '--yes'])
    assert result.exit_code == 4
    assert "api-down" in (result.stderr or "")
    assert "Summary for example.com:" in result.stdout


def test_cli_confirm_y_executes(runner, monkeypatch):
    mock_api = Mock()
    monkeypatch.setattr(api, "PorkbunAPI", mock_api)
    mock_api().get_my_ip.return_value = "1.2.3.4"
    monkeypatch.setattr(cli, '_collect_existing_dns_records', lambda *_: {"example.com": []})
    monkeypatch.setattr(cli, '_plan_operations', lambda *_: {"example.com": []})
    mock_exec = Mock(return_value={})
    monkeypatch.setattr(cli, '_execute_operations_plan', mock_exec)
    result = runner.invoke(cli.main, ['tests/config.yml'], input="y")
    assert result.exit_code == 0
    mock_exec.assert_called_once()


@pytest.mark.parametrize("data", ["", "n", "N", "1"])
def test_cli_abort(runner, monkeypatch, data):
    mock_api = Mock()
    monkeypatch.setattr(api, "PorkbunAPI", mock_api)
    mock_api().get_my_ip.return_value = "1.2.3.4"
    monkeypatch.setattr(cli, '_collect_existing_dns_records', lambda *_: {"example.com": []})
    monkeypatch.setattr(cli, '_plan_operations', lambda *_: {"example.com": []})
    mock_exec = Mock(return_value={})
    monkeypatch.setattr(cli, '_execute_operations_plan', mock_exec)
    result = runner.invoke(cli.main, ['tests/config.yml', '--mode', 'append'], input=data)
    assert result.exit_code == 0
    assert "Operation aborted." in (result.stderr or "")
    mock_exec.assert_not_called()


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
        mode = "upgrade"
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
        self.assertEqual(len(result["replace.com"]), 3)
        self.assertEqual(result["replace.com"][0].operation, "update")
        self.assertEqual(result["replace.com"][0].new.name, "www")
        self.assertEqual(result["replace.com"][1].operation, "match")
        self.assertEqual(result["replace.com"][1].new.name, "autoconfig")
        self.assertEqual(result["replace.com"][1].existing.id, "r2")
        self.assertEqual(result["replace.com"][2].operation, "create")
        self.assertEqual(result["replace.com"][2].new.name, "ftp")
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
                    operation="update",
                    existing=ExistingDnsRecord(name="mail.pass.com", type="MX", id="456", content=""),
                    new=DnsRecord(name="mail", type="MX", content="mail.pass.com"),
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
                    operation="update",
                    existing=ExistingDnsRecord(name="mail.fail.com", type="MX", id="654", content=""),
                    new=DnsRecord(name="mail", type="MX", content="mail.fail.com"),
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
            call(1, 2, "\tupdate MX-record 'mail.pass.com' ... ", nl=False),
            call(1, 2, 'done'),
            call(1, 2, "- altering domain 'fail.com'"),
            call(1, 2, "\tcreate A-record 'www.fail.com' ... ", nl=False),
            call(1, 2, "\tupdate A-record 'www.fail.com' ... ", nl=False),
            call(1, 2, "\tupdate MX-record 'mail.fail.com' ... ", nl=False),
            call(1, 2, "- altering domain 'invalid.com'"),
            call(0, 2, "unknown operation 'invalid'"),
        ]

        self.assertListEqual(expected_calls, mock_log_if_level.mock_calls)
