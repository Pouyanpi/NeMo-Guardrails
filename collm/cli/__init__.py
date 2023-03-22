import logging

import typer

from collm.cli.chat import run_chat

app = typer.Typer()


@app.command()
def chat(
    config: str = typer.Option(
        default="config",
        exists=True,
        help="A configuration file to use.",
    ),
    verbose: bool = typer.Option(
        default=False,
        help="If the chat should be verbose and output the prompts",
    ),
):
    """Starts an interactive chat session."""
    if verbose:
        logging.basicConfig(level=logging.INFO)

    typer.echo("Starting the chat...")
    run_chat(config_path=config, verbose=verbose)


@app.command()
def server():
    """Starts the CoLLM server."""

    typer.echo("Not yet implemented.")
