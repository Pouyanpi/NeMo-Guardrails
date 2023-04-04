import logging

import typer
import uvicorn

from colangflows.cli.chat import run_chat
from colangflows.server import api

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
def server(
    port: int = typer.Option(
        default=8000, help="The port that the server should listen on. "
    ),
):
    """Starts a Colang Flows server."""

    uvicorn.run(api.app, port=port, log_level="info", host="0.0.0.0")
