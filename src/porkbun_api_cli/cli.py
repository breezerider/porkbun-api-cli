#!/usr/bin/env python3

import sys

import click

from . import __version__
from . import api as PorkbunAPI
from . import utils


def _print_version(ctx, param, value):
    if not value or ctx.resilient_parsing:
        return
    click.echo(f'Version {__version__}')
    ctx.exit(0)


def _log_if_level(level, verbosity, message, file=None, nl=True):
    if verbosity >= level:
        click.echo(message, file=file, nl=nl)


def _collect_existing_dns_records(api, domain_names, verbose):
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


def _plan_operations(mode, verbose, existing_domains, config_domains):
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

        operations = []
        processed = []
        for record in config_dns_records:
            existing = filter(lambda x: utils.compare_record_by_name_type(domain_name, record, x), existing_dns_records)
            existing_found = False
            for entry in existing:
                existing_found = True
                processed.append(entry)
                if utils.compare_record_by_content_ttl_prio(record, entry):
                    _log_if_level(
                        3,
                        verbose,
                        f"\t- found matching {record['type']}-record '{record['name']}.{domain_name}'",
                    )
                elif utils.operation_allowed_by_mode("update", mode):
                    _log_if_level(
                        2,
                        verbose,
                        f"\t- update {record['type']}-record '{record['name']}.{domain_name}'",
                    )
                    operations.append({"operation": "update", "new": record, "existing": entry})
            if not existing_found and utils.operation_allowed_by_mode("create", mode):
                _log_if_level(2, verbose, f"\t- create {record['type']}-record '{record['name']}.{domain_name}'")
                operations.append({"operation": "create", "new": record, "existing": None})

        # check if additional exntries should be removed
        if utils.operation_allowed_by_mode("delete", mode):
            for record in existing_dns_records:
                if record not in processed:
                    _log_if_level(2, verbose, f"\t- delete {record['type']}-record '{record['name']}'")
                    operations.append({"operation": "delete", "new": None, "existing": record})

        planned_operations[domain_name] = operations

    return planned_operations


def _execute_operations_plan(api, verbose, operations_plan):
    _log_if_level(1, verbose, "\n\tEXECUTION\n")
    for domain_name, operations in operations_plan.items():
        _log_if_level(1, verbose, f"- altering domain '{domain_name}'")
        for operation in operations:
            op = operation["operation"]
            if op not in ["create", "update", "delete"]:
                _log_if_level(0, verbose, f"unknown operation '{op}'")
                continue

            if op in ["create", "update"]:
                record = operation["new"]
                if len(record["name"]):
                    name = f"{record['name']}.{domain_name}"
                else:
                    name = domain_name
            elif op == "delete":
                record = operation["existing"]
                name = record["name"]
            _log_if_level(1, verbose, f"\t{op} {record['type']}-record '{name}' ... ", nl=False)

            try:
                if op == "create":
                    api.create_record(domain_name, record)
                elif op == "update":
                    api.update_record(domain_name, operation["existing"]["id"], record)
                elif op == "delete":
                    _log_if_level(0, verbose, f"{op} operation is not implemented - skipped")
            except RuntimeError as e:
                _log_if_level(0, verbose, f"querying Porkbun API for domain '{domain_name}' failed: {str(e)}")
            else:
                if op != "delete":
                    _log_if_level(1, verbose, "done")


@click.command()
@click.argument("config_file", type=click.Path(exists=True))
@click.option(
    "-m",
    "--mode",
    type=click.Choice(
        [
            "append",
            "replace",
            "update",
            "upgrade",
        ]
    ),
    default="append"
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
def main(config_file, mode, dry_run, verbose, arguments):
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
    """  # noqa: E501, B950

    # load configuration
    try:
        config = utils.load_config(config_file)
    except Exception as e:
        click.echo(f"failed to load configuration from {config_file}: " + str(e))
        sys.exit(1)

    api = PorkbunAPI.PorkbunAPI(**config["api"])

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
    domain_names = [entry["name"] for entry in config["domains"]]

    existing_domains = _collect_existing_dns_records(api, domain_names, verbose)
    config_domains = {x["name"]: x["records"] for x in config["domains"]}

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
