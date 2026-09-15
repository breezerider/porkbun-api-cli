#!/usr/bin/env python3
from __future__ import annotations

import os
import sys
from typing import TextIO

import click

from . import __version__
from . import api as PorkbunAPI
from . import utils
from .utils import DnsRecord
from .utils import ExistingDnsRecord
from .utils import PlanEntry


def _print_version(ctx: click.Context, param: click.Parameter, value: bool) -> None:
    if not value or ctx.resilient_parsing:
        return
    click.echo(f'Version {__version__}')
    ctx.exit(0)


def _log_if_level(level: int, verbosity: int, message: str, file: TextIO | None = None, nl: bool = True) -> None:
    if verbosity >= level:
        click.echo(message, file=file, nl=nl)


def _use_color() -> bool:
    return sys.stdout.isatty() and os.environ.get("NO_COLOR") is None


def _colorize(text: str, color: str) -> str:
    if _use_color():
        return click.style(text, fg=color)
    return text


_SYMBOL_COLORS: dict[str, str] = {
    "NEW": "green",
    "UPD": "blue",
    "DEL": "red",
    "OK ": "green",
    "ERR": "bright_red",
    "SKP": "yellow",
}


def _collect_existing_dns_records(
    api: PorkbunAPI.PorkbunAPI, domain_names: list[str], verbose: int
) -> dict[str, list[ExistingDnsRecord] | None]:
    result = {}
    for domain_name in domain_names:
        _log_if_level(0, verbose, f"- querying records for '{domain_name}' .. ", nl=False)

        try:
            existing_records = api.list_dns_records(domain_name)
        except RuntimeError as e:
            existing_records = None
            _log_if_level(0, verbose, "failed")
            _log_if_level(0, verbose, f"Querying records for '{domain_name}' failed: {str(e)}", file=sys.stderr)
        else:
            _log_if_level(0, verbose, "done")

        result[domain_name] = existing_records

    return result


def _plan_operations(
    mode: str,
    verbose: int,
    existing_domains: dict[str, list[ExistingDnsRecord] | None],
    config_domains: dict[str, list[DnsRecord]],
) -> dict[str, list[PlanEntry] | None]:
    all_domain_names = sorted({*existing_domains.keys(), *config_domains.keys()})

    planned_operations = {}
    for domain_name in all_domain_names:
        existing_dns_records = existing_domains.get(domain_name, None)
        config_dns_records = config_domains.get(domain_name, None)

        if existing_dns_records is None:
            _log_if_level(0, verbose, f"skipping '{domain_name}': querying existing records failed")
            planned_operations[domain_name] = None
            continue
        if config_dns_records is None:
            _log_if_level(1, verbose, f"skipping '{domain_name}': not included in current configuration")
            planned_operations[domain_name] = None
            continue

        operations: list[PlanEntry] = []
        for target_record in config_dns_records:
            existing = [
                x for x in existing_dns_records if utils.compare_record_by_name_type(domain_name, target_record, x)
            ]
            existing_found = False
            for entry in existing:
                existing_found = True
                target_fqdn = f"{target_record.name}.{domain_name}" if len(target_record.name) else domain_name
                if utils.compare_record_by_content_ttl_prio(target_record, entry):
                    if target_record.ttl == 0:
                        _log_if_level(
                            0,
                            verbose,
                            f"ttl=0 in config treated as 'use default'; ttl comparison skipped for {target_fqdn}",
                            file=sys.stderr,
                        )
                    if target_record.prio is None and entry.prio not in (None, 0):
                        _log_if_level(
                            0,
                            verbose,
                            f"prio omitted in config; server returned prio={entry.prio} for {target_fqdn}",
                            file=sys.stderr,
                        )
                    operations.append(PlanEntry(operation="match", new=target_record, existing=entry))
                elif utils.operation_allowed_by_mode("update", mode):
                    operations.append(PlanEntry(operation="update", new=target_record, existing=entry))
            if not existing_found and utils.operation_allowed_by_mode("create", mode):
                operations.append(PlanEntry(operation="create", new=target_record, existing=None))

        planned_operations[domain_name] = operations

    return planned_operations


def _execute_operations_plan(
    api: PorkbunAPI.PorkbunAPI, verbose: int, operations_plan: dict[str, list[PlanEntry] | None]
) -> dict[str, int]:
    """Execute the operations plan. Returns per-domain failure counts."""
    _log_if_level(1, verbose, "\n\tEXECUTION\n")
    failed_by_domain: dict[str, int] = {}
    for domain_name, operations in operations_plan.items():
        if operations is None:
            continue
        _log_if_level(1, verbose, f"- altering domain '{domain_name}'")
        for operation in operations:
            op = operation.operation
            if op == "match":
                continue
            if op not in ["create", "update"]:
                _log_if_level(0, verbose, f"unknown operation '{op}'")
                continue

            new = operation.new
            # ty: narrow — new is non-None on create/update branch
            assert new is not None
            name = f"{new.name}.{domain_name}" if len(new.name) else domain_name
            _log_if_level(1, verbose, f"\t{op} {new.type}-record '{name}' ... ", nl=False)

            try:
                if op == "create":
                    api.create_record(domain_name, new)
                else:  # op == "update"
                    existing = operation.existing
                    # ty: narrow — existing is non-None on update branch (update requires a matched record)
                    assert existing is not None
                    api.update_record(domain_name, existing.id, new)
            except RuntimeError as e:
                click.echo(f"querying Porkbun API for domain '{domain_name}' failed: {e}", file=sys.stderr)
                failed_by_domain[domain_name] = failed_by_domain.get(domain_name, 0) + 1
            else:
                _log_if_level(1, verbose, "done")

    return failed_by_domain


def _render_plan(
    mode: str,
    verbose: int,
    operations_plan: dict[str, list[PlanEntry] | None],
) -> None:
    for domain, operations in operations_plan.items():
        if operations is None:
            continue
        rows: list[str] = []
        for entry in operations:
            op = entry.operation
            if op == "match":
                if verbose < 2:
                    continue
                symbol = "OK "
            elif op == "create":
                symbol = "NEW"
            elif op == "update":
                symbol = "UPD"
            else:
                continue
            rec = entry.new
            # ty: narrow — new is non-None for create/update/match entries
            assert rec is not None
            fqdn = f"{rec.name}.{domain}" if len(rec.name) else domain
            content = f"{rec.type} {fqdn} {rec.content}"
            rows.append(f"  {_colorize(symbol, _SYMBOL_COLORS[symbol])}  {content}")
        if rows:
            click.echo(f"Plan for {domain} ({mode} mode):")
            for row in rows:
                click.echo(row)


def _render_summary(
    domain: str,
    operations: list[PlanEntry] | None,
    verbose: int,
    failed_count: int = 0,
) -> None:
    if operations is None:
        return
    if operations == []:
        click.echo(f"Summary for {domain}: no records found")
        return
    created = sum(1 for e in operations if e.operation == "create")
    updated = sum(1 for e in operations if e.operation == "update")
    matched = sum(1 for e in operations if e.operation == "match")
    failed = failed_count
    parts = []
    if verbose >= 1 or created:
        parts.append(f"{_colorize(str(created), _SYMBOL_COLORS['NEW'])} created")
    if verbose >= 1 or updated:
        parts.append(f"{_colorize(str(updated), _SYMBOL_COLORS['UPD'])} updated")
    if verbose >= 1 or matched:
        parts.append(f"{_colorize(str(matched), _SYMBOL_COLORS['OK '])} matched")
    if verbose >= 1 or failed:
        parts.append(f"{_colorize(str(failed), _SYMBOL_COLORS['ERR'])} failed")
    click.echo(f"Summary for {domain}: {', '.join(parts)}")


@click.command()
@click.argument("config_file", type=click.Path(exists=True))
@click.option(
    "-m",
    "--mode",
    type=click.Choice([
        "append",
        "replace",
        "update",
        "upgrade",
    ]),
    default="append",
    help=("Operation mode: append (default), update, upgrade. 'replace' is not implemented, use 'upgrade'."),
)
@click.option(
    "-n",
    "--dry-run",
    is_flag=True,
    help="Perform a trial run; exits non-zero (code 3) if any changes would be needed",
)
@click.option(
    "-y",
    "--yes",
    is_flag=True,
    help="Skip confirmation prompt",
)
@click.option(
    "-V",
    "--version",
    is_flag=True,
    help="Print tool version and exit",
    callback=_print_version,
    expose_value=False,
    is_eager=True,
)
@click.option("-v", "--verbose", count=True, help="Output verbosity")
def main(config_file: str, mode: str, dry_run: bool, yes: bool, verbose: int) -> None:
    """CLI client for managing domains with Porkbun through API calls.

    It can create, edit and list DNS records following a configuration
    provided in a YAML file. The client is flexible and can restrict
    its operations to only a subset choosen by the user by supporting
    several operation modes:

    * append -- only new entries are created preserving existing entries
                unchanged
    * replace -- not implemented, use 'upgrade'
    * update -- only update existing entries without creating or removing
                entries that are not listed in the configuration
    * upgrade -- create new entries or update exising but do not remove
                 entries that are not listed in the configuration
    """  # noqa: E501

    if mode == "replace":
        raise click.UsageError("replace mode is not implemented, use 'upgrade'")

    if yes and dry_run:
        raise click.UsageError("--yes and --dry-run are mutually exclusive")

    # load configuration
    try:
        config = utils.load_config(config_file)
    except Exception as e:
        click.echo(f"failed to load configuration from {config_file}: {e}", file=sys.stderr)
        sys.exit(1)

    api = PorkbunAPI.PorkbunAPI(
        apikey=config.api.apikey,
        secretapikey=config.api.secretapikey,
        endpoint=config.api.endpoint,
    )

    if dry_run:
        click.echo("dry run requested, enable verbose output")
        verbose = max(2, verbose)

    # test API config
    try:
        ip = api.get_my_ip()
        _log_if_level(1, verbose, f"IP address reported by API '{ip}'")
    except RuntimeError as e:
        click.echo(f"querying Porkbun API failed: {e}", file=sys.stderr)
        sys.exit(1)

    # extract domain domain names
    domain_names = [d.name for d in config.domains]

    existing_domains = _collect_existing_dns_records(api, domain_names, verbose)
    config_domains = {d.name: d.records for d in config.domains}

    operations_plan = _plan_operations(mode, verbose, existing_domains, config_domains)

    _render_plan(mode, verbose, operations_plan)

    if dry_run:
        click.echo("dry run requested, skipping execution")
        has_changes = any(
            op is not None and any(e.operation in {"create", "update"} for e in op) for op in operations_plan.values()
        )
        sys.exit(3 if has_changes else 0)

    if not yes:
        click.echo("Would you like to proceed? [yN]: ", nl=False)
        confirm = click.getchar()
        click.echo()
        if confirm.lower() != "y":
            click.echo("Operation aborted.", file=sys.stderr)
            sys.exit(0)

    failed_by_domain = _execute_operations_plan(api, verbose, operations_plan)
    failed_any = bool(failed_by_domain)

    for domain, operations in operations_plan.items():
        if operations is None:
            continue
        # ty: narrow — non-None operations here (executor skips None entries)
        domain_failed = failed_by_domain.get(domain, 0)
        _render_summary(domain, operations, verbose, domain_failed)

    sys.exit(4 if failed_any else 0)


if __name__ == "__main__":
    main()
