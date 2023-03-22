import typer

from collm.cli.chat import run_chat

app = typer.Typer()


@app.command()
def chat(
    config: str = typer.Option(
        default=...,
        exists=True,
        help="A configuration file to use.",
    ),
):
    """Starts an interactive chat session."""

    typer.echo("Starting the chat...")
    run_chat(config_path=config)


@app.command()
def server():
    """Starts the CoLLM server."""

    typer.echo("Not yet implemented.")
