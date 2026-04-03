#!/usr/bin/env python3
"""
Template script for odooly-based operations.

Usage:
    python template.py -c ~/odooly.ini --env ENV [OPTIONS]

Edit this template to implement your custom logic.
"""

import pathlib

import click
import odooly


@click.command()
@click.option("-c", "--config", default="odooly.ini", help="Specify alternate config file (default: odooly.ini).")
@click.option("--env", required=True, help="Odooly environment name from config.")
@click.option("--dry-run", is_flag=True, default=False, help="Show what would happen without writing.")
def run(config, env, dry_run):
    """Template script - edit this description for your script."""
    # Set config file path before creating client (must be a Path object)
    odooly.Client._config_file = pathlib.Path(config).expanduser()
    client = odooly.Client.from_config(env)

    click.echo(f"Connected to environment: {env}")
    click.echo(f"Database: {client.env.db_name}")
    click.echo(f"User: {client.env.user}")

    if dry_run:
        click.echo("[dry-run] Preview mode - no changes will be made.")

    # === YOUR CUSTOM LOGIC HERE ===
    # Examples:
    # - Query records: client.env["model.name"].search(domain)
    # - Read fields: record.read(["field1", "field2"])
    # - Write data: record.write({"field": "value"})
    # - Execute methods: model.method_name()

    click.echo("\nDone.")


if __name__ == "__main__":
    run()
