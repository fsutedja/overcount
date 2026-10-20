"""Command-line interface: `uv run overcount --help`."""

from pathlib import Path
from typing import Annotated

import typer

from .publish import build_bank, stale_files, write_bank

REPO_ROOT = Path(__file__).resolve().parents[3]

app = typer.Typer(
    help="Overcount content pipeline: verify problem templates and publish the static bank.",
    no_args_is_help=True,
)


@app.callback()
def main() -> None:
    """Overcount content pipeline."""


CONTENT_DIR = REPO_ROOT / "content"
BANK_DIR = REPO_ROOT / "web" / "public" / "bank"


@app.command()
def build(
    content: Annotated[Path, typer.Option(help="Folder with families/<slug>/family.json")] = CONTENT_DIR,
    out: Annotated[Path, typer.Option(help="Where the web app loads the bank from")] = BANK_DIR,
    check: Annotated[bool, typer.Option(help="Only check the committed bank is up to date (CI)")] = False,
) -> None:
    """Build the problem bank from content/ into web/public/bank/."""
    bank = build_bank(content)
    if check:
        stale = stale_files(bank, out)
        if stale:
            typer.echo("The committed bank is out of date. Run `uv run overcount build`:", err=True)
            for path in stale:
                typer.echo(f"  {path}", err=True)
            raise typer.Exit(1)
        typer.echo("Bank is up to date.")
        return
    write_bank(bank, out)
    typer.echo(f"Wrote {len(bank.files)} files to {out}")
