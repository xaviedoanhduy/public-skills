#!/usr/bin/env python3
"""
List Odoo modules from an environment.

Usage:
    python list_modules.py -c ~/odooly.ini --env ENV [OPTIONS]

Examples:
    # List installed non-core modules
    python list_modules.py -c ~/odooly.ini --env production

    # List all installed modules (including core)
    python list_modules.py -c ~/odooly.ini --env production --include-core

    # List all modules regardless of state
    python list_modules.py -c ~/odooly.ini --env production --no-installed

    # With repo detection and CLOC from local project
    python list_modules.py -c ~/odooly.ini --env production --project-dir ~/code/project --format csv --columns repo,module,version,cloc
"""

import csv
import pathlib
import sys

import click
import odooly
from manifestoo_core.core_addons import is_core_ce_addon, is_core_ee_addon
from manifestoo_core.odoo_series import OdooSeries

import cloc as cloc_module


AVAILABLE_COLUMNS = ["module", "state", "repo", "description", "version", "author", "website", "cloc"]

# Map column names to ir.module.module field names
COLUMN_TO_FIELD = {
    "module": "name",
    "state": "state",
    "repo": None,  # computed
    "description": "shortdesc",
    "version": "installed_version",
    "author": "author",
    "website": "website",
    "cloc": None,  # computed from local files
}

COLUMN_WIDTHS = {
    "module": 40,
    "state": 12,
    "repo": 12,
    "description": 40,
    "version": 16,
    "author": 25,
    "website": 30,
    "cloc": 8,
}

# Map directory names to canonical repo names
ORG_REPO_MAPPING = {
    "project": "local-src",
}


def get_repo(module_name, odoo_series):
    if is_core_ce_addon(module_name, odoo_series):
        return "odoo"
    if is_core_ee_addon(module_name, odoo_series):
        return "enterprise"
    return "other"


def get_repo_and_cloc(path, module):
    """Get repo name and CLOC count for a module in a given addons path."""
    manifest = path / module / "__manifest__.py"
    if not manifest.exists():
        return None, None
    org_repo = path.name
    if ORG_REPO_MAPPING.get(org_repo):
        org_repo = ORG_REPO_MAPPING[org_repo]
    elif org_repo.startswith("oca-"):
        org_repo = org_repo.replace("oca-", "")
    c = cloc_module.Cloc()
    c.count_path(str(path / module))
    code = sum(c.code.values())
    return org_repo, code


def build_local_module_info(project_dir):
    """Build a dict of {module_name: (repo, cloc)} from local project directory."""
    from odoo_addons_path import get_addons_path

    base_path = pathlib.Path(project_dir)
    addons_path_str = get_addons_path(base_path)
    addons_paths = addons_path_str.split(",")

    module_info = {}
    for path_str in addons_paths:
        path = pathlib.Path(path_str)
        if not path.is_dir():
            continue
        for entry in path.iterdir():
            if not entry.is_dir():
                continue
            module_name = entry.name
            if module_name in module_info:
                continue
            org_repo, code = get_repo_and_cloc(path, module_name)
            if org_repo is None:
                continue
            # local-src heuristic: "project" dir directly under base_path
            if org_repo == path.name and path.parent == base_path:
                org_repo = "local-src"
            module_info[module_name] = (org_repo, code)
    return module_info


def get_column_value(record, column, odoo_series, local_info=None):
    if column == "repo":
        if local_info and record["name"] in local_info:
            return local_info[record["name"]][0]
        return get_repo(record["name"], odoo_series)
    if column == "state":
        return (record.get("state") or "").upper()
    if column == "cloc":
        if local_info and record["name"] in local_info:
            return local_info[record["name"]][1]
        return ""
    field = COLUMN_TO_FIELD[column]
    return record.get(field) or ""


@click.command()
@click.option("-c", "--config", default="odooly.ini", help="Specify alternate config file (default: odooly.ini).")
@click.option("--env", required=True, help="Odooly environment name from config.")
@click.option("--installed/--no-installed", default=True, help="Filter installed modules only (default: True).")
@click.option("--include-core", is_flag=True, default=False, help="Include core CE/EE modules (default: False).")
@click.option("--format", "fmt", type=click.Choice(["table", "csv"]), default="table", help="Output format (default: table).")
@click.option("--columns", default="module,state,repo,description", help=f"Comma-separated columns to display. Available: {','.join(AVAILABLE_COLUMNS)}")
@click.option("--project-dir", default=None, type=click.Path(exists=True), help="Local project directory for repo detection and CLOC counting.")
@click.option("--output", default=None, type=click.Path(), help="Write output to a file instead of stdout.")
def run(config, env, installed, include_core, fmt, columns, project_dir, output):
    """List Odoo modules from an environment."""
    odooly.Client._config_file = pathlib.Path(config).expanduser()
    client = odooly.Client.from_config(env)

    is_csv = fmt == "csv"
    if not is_csv:
        click.echo(f"Connected to environment: {env}")
        click.echo(f"Database: {client.env.db_name}")
        click.echo(f"Server version: {client.server_version}")

    # Detect Odoo series from server version (e.g. "18.0+e" -> "18.0")
    major_minor = f"{int(client.version_info)}.0"
    odoo_series = OdooSeries(major_minor)

    # Build local module info if project-dir is provided
    local_info = None
    if project_dir:
        if not is_csv:
            click.echo(f"Scanning project directory: {project_dir}")
        local_info = build_local_module_info(project_dir)
        if not is_csv:
            click.echo(f"Found {len(local_info)} modules locally")

    domain = []
    if installed:
        domain.append(("state", "=", "installed"))

    cols = [c.strip() for c in columns.split(",")]
    for c in cols:
        if c not in AVAILABLE_COLUMNS:
            raise click.BadParameter(f"Unknown column '{c}'. Available: {','.join(AVAILABLE_COLUMNS)}")

    if "cloc" in cols and not project_dir:
        raise click.UsageError("--project-dir is required when using the 'cloc' column.")

    # Collect the ir.module.module fields we need to read
    fields_to_read = {"name"}  # always needed for filtering
    for c in cols:
        field = COLUMN_TO_FIELD.get(c)
        if field:
            fields_to_read.add(field)

    Module = client.env["ir.module.module"]
    modules = Module.search(domain)
    records = modules.read(list(fields_to_read))

    if not include_core:
        records = [
            r for r in records
            if not is_core_ce_addon(r["name"], odoo_series)
            and not is_core_ee_addon(r["name"], odoo_series)
        ]

    records.sort(key=lambda r: r["name"])

    if fmt == "csv":
        out = open(output, "w", newline="") if output else sys.stdout
        try:
            writer = csv.writer(out)
            writer.writerow(cols)
            for r in records:
                writer.writerow([get_column_value(r, c, odoo_series, local_info) for c in cols])
        finally:
            if output:
                out.close()
    else:
        header = "  ".join(f"{c.capitalize():<{COLUMN_WIDTHS.get(c, 20)}}" for c in cols)
        click.echo(f"\n{header}")
        click.echo("-" * len(header))
        for r in records:
            row = "  ".join(
                f"{str(get_column_value(r, c, odoo_series, local_info)):<{COLUMN_WIDTHS.get(c, 20)}}"
                for c in cols
            )
            click.echo(row)
        click.echo(f"\nTotal: {len(records)} modules")


if __name__ == "__main__":
    run()
