#!/usr/bin/env python3

import json
import pathlib
import click
import odooly
import sys


def _get_images(client_from, domain=None):
    domain = domain or []
    ProductTemplate_from = client_from.env["product.template"]
    return ProductTemplate_from.search(domain)


def _copy_images(client_from, client_to, product_template_id, dry_run=False):

    ProductTemplate_from = client_from.env["product.template"]
    ProductTemplate_to = client_to.env["product.template"]

    product_template_id = int(product_template_id)

    try:
        p_from = ProductTemplate_from.browse(product_template_id)
    except Exception as e:
        click.echo(
            f"product.template does not exist: {product_template_id}. Error: {e}"
        )
        return "fail"

    if not p_from.image:
        click.echo(
            f"Skipped product.template with no image: {product_template_id}."
        )
        return "skip"

    p_to = None
    if p_from.barcode:
        p_to = ProductTemplate_to.search([
            ["barcode", "=", p_from.barcode]
        ])
        if len(p_to) > 1:
            click.echo(
                f"Found multiple products with this barcode: {p_from.barcode}."
            )
            p_to = None

    if not p_to:
        click.echo(f"Trying with name instead.")
        p_to = ProductTemplate_to.search([
            ["name", "=", p_from.name]
        ])
        if len(p_to) > 1:
            click.echo(
                f"Found multiple products with this name: {p_from.name}."
            )
            p_to = None

    if not p_to:
        click.echo(f"Corresponding product not found: {p_from.id}.")
        return "fail"

    if dry_run:
        click.echo(
            f"[dry-run] Would copy image from {p_from.id} to {p_to.id}."
        )
        return "success"

    p_to.write({
        "image": p_from.image,
        "image_medium": p_from.image_medium,
        "image_small": p_from.image_small,
    })

    click.echo(f"Copied product.template picture {p_to.id}.")

    return "success"


@click.command()
@click.option("-c", "--config", default="odooly.ini", help="Specify alternate config file (default: odooly.ini).")
@click.option("--env-from", required=True, help="Source odooly environment name.")
@click.option("--env-to", required=True, help="Destination odooly environment name.")
@click.option("--product-template-id", default=None, help="Copy a single product template by ID.")
@click.option("--domain", default=None, help='Custom domain filter as JSON, e.g. \'[["image", "!=", false]]\'.')
@click.option("--dry-run", is_flag=True, default=False, help="Show what would be copied without writing.")
def run(config, env_from, env_to, product_template_id, domain, dry_run):
    # Set config file path before creating clients (must be a Path object)
    odooly.Client._config_file = pathlib.Path(config).expanduser()
    client_from = odooly.Client.from_config(env_from)
    client_to = odooly.Client.from_config(env_to)

    results = {"success": 0, "skip": 0, "fail": 0}

    if product_template_id:
        result = _copy_images(client_from, client_to, product_template_id, dry_run=dry_run)
        if result:
            results[result] += 1
    else:
        if domain:
            try:
                search_domain = json.loads(domain)
            except json.JSONDecodeError as e:
                click.echo(f"Invalid domain JSON: {e}", err=True)
                sys.exit(1)
        else:
            search_domain = [["image", "!=", False]]

        image_ids = _get_images(client_from, search_domain)
        total = len(image_ids)
        click.echo(f"Number of images to copy: {total}.")

        for i, record in enumerate(image_ids, 1):
            result = _copy_images(client_from, client_to, record.id, dry_run=dry_run)
            if result:
                results[result] += 1
            if i % 10 == 0 or i == total:
                click.echo(f"Progress: {i}/{total}")

    click.echo(
        f"\nSummary: {results['success']} copied, "
        f"{results['skip']} skipped, {results['fail']} failed."
    )


if __name__ == "__main__":
    run()
