#!/usr/bin/env python3
from __future__ import annotations

import sys
from typing import TextIO

import click

from . import __version__
from . import api as PorkbunAPI
from . import utils
from .utils import DnsRecord
from .utils import ExistingDnsRecord
from .utils import Operation


def _print_version(ctx: click.Context, param: click.Parameter, value: bool) -> None:
    if not value or ctx.resilient_parsing:
        return
    click.echo(f'Version {__version__}')
    ctx.exit(0)


def _log_if_level(level: int, verbosity: int, message: str, file: TextIO | None = None, nl: bool = True) -> None:
    if verbosity >= level:
        click.echo(message, file=file, nl=nl)


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
) -> dict[str, list[Operation] | None]:
    all_domain_names = sorted({*existing_domains.keys(), *config_domains.keys()})

    _log_if_level(1, verbose, "\n\tPROCESSING EXISTING RECORDS\n")
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

        operations: list[Operation] = []
        processed = []
        for target_record in config_dns_records:
            existing = [
                x for x in existing_dns_records if utils.compare_record_by_name_type(domain_name, target_record, x)
            ]
            existing_found = False
            for entry in existing:
                existing_found = True
                processed.append(entry)
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
                    _log_if_level(
                        3,
                        verbose,
                        f"\t- found matching {target_record.type}-record '{target_fqdn}'",
                    )
                elif utils.operation_allowed_by_mode("update", mode):
                    _log_if_level(
                        2,
                        verbose,
                        f"\t- update {target_record.type}-record '{target_fqdn}'",
                    )
                    operations.append(Operation(operation="update", new=target_record, existing=entry))
            if not existing_found and utils.operation_allowed_by_mode("create", mode):
                target_fqdn = f"{target_record.name}.{domain_name}" if len(target_record.name) else domain_name
                _log_if_level(2, verbose, f"\t- create {target_record.type}-record '{target_fqdn}'")
                operations.append(Operation(operation="create", new=target_record, existing=None))

        # check if additional exntries should be removed
        if utils.operation_allowed_by_mode("delete", mode):
            for entry in existing_dns_records:
                if entry not in processed:
                    _log_if_level(2, verbose, f"\t- delete {entry.type}-record '{entry.name}'")
                    operations.append(Operation(operation="delete", new=None, existing=entry))

        planned_operations[domain_name] = operations

    return planned_operations


def _execute_operations_plan(
    api: PorkbunAPI.PorkbunAPI, verbose: int, operations_plan: dict[str, list[Operation] | None]
) -> None:
    _log_if_level(1, verbose, "\n\tEXECUTION\n")
    for domain_name, operations in operations_plan.items():
        if operations is None:
            continue
        _log_if_level(1, verbose, f"- altering domain '{domain_name}'")
        for operation in operations:
            op = operation.operation
            if op not in ["create", "update", "delete"]:
                _log_if_level(0, verbose, f"unknown operation '{op}'")
                continue

            if op == "delete":
                existing = operation.existing
                # ty: narrow — existing is non-None on delete branch
                assert existing is not None
                name = existing.name
                _log_if_level(1, verbose, f"\t{op} {existing.type}-record '{name}' ... ", nl=False)
                _log_if_level(0, verbose, f"{op} operation is not implemented - skipped")
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
                _log_if_level(0, verbose, f"querying Porkbun API for domain '{domain_name}' failed: {str(e)}")
            else:
                _log_if_level(1, verbose, "done")


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
)
@click.option("-n", "--dry-run", is_flag=True, help="Perform a trial run without any changes made")
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
@click.argument("arguments", nargs=-1)
def main(config_file: str, mode: str, dry_run: bool, verbose: int, arguments: tuple[str, ...]) -> None:
    """CLI client for managing domains with Porkbun through API calls.

    It can create, edit and list DNS records following a configuration
    provided in a YAML file. The client is flexible and can restrict
    its operations to only a subset choosen by the user by supporting
    several operation modes:

    * append -- only new entries are created preserving existing entries
                unchanged
    * replace -- replace all existing entries with user configuration
    * update -- only update existing entries without creating or removing
                entries that are not listed in the configuration
    * upgrade -- create new entries or update exising but do not remove
                 entries that are not listed in the configuration
    """  # noqa: E501

    # load configuration
    try:
        config = utils.load_config(config_file)
    except Exception as e:
        click.echo(f"failed to load configuration from {config_file}: " + str(e))
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
        _log_if_level(0, verbose, f"querying Porkbun API failed: {str(e)}")
        sys.exit(1)

    # extract domain domain names
    domain_names = [d.name for d in config.domains]

    existing_domains = _collect_existing_dns_records(api, domain_names, verbose)
    config_domains = {d.name: d.records for d in config.domains}

    operations_plan = _plan_operations(mode, verbose, existing_domains, config_domains)

    if dry_run:
        click.echo("dry run requested, skipping execution")
        sys.exit(0)
    else:
        click.echo("Would you like to proceed? [yN]: ", nl=False)
        confirm = click.getchar()
        click.echo()
        if confirm.lower() != 'y':
            _log_if_level(0, verbose, "Operation aborted.", file=sys.stderr)
            sys.exit(0)

    _execute_operations_plan(api, verbose, operations_plan)


if __name__ == "__main__":
    main()
