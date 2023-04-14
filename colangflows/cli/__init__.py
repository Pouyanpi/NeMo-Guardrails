# SPDX-FileCopyrightText: Copyright (c) 2023 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: Apache-2.0
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import logging
from typing import List

import typer
import uvicorn

from colangflows.actions_server import actions_server
from colangflows.cli.chat import run_chat
from colangflows.server import api

app = typer.Typer()


@app.command()
def chat(
    config: List[str] = typer.Option(
        default=["config"],
        exists=True,
        help="Path to a directory containing configuration files to use. Can also point to a single configuration file.",
    ),
    verbose: bool = typer.Option(
        default=False,
        help="If the chat should be verbose and output the prompts",
    ),
):
    """Starts an interactive chat session."""
    if verbose:
        logging.basicConfig(level=logging.INFO)

    if len(config) > 1:
        typer.secho(f"Multiple configurations are not supported.", fg=typer.colors.RED)
        typer.echo("Please provide a single .yml file or a folder.")
        raise typer.Exit(1)

    typer.echo("Starting the chat...")
    run_chat(config_path=config[0], verbose=verbose)


@app.command()
def server(
    port: int = typer.Option(
        default=8000, help="The port that the server should listen on. "
    ),
):
    """Starts a Colang Flows server."""

    uvicorn.run(api.app, port=port, log_level="info", host="0.0.0.0")


@app.command("actions-server")
def action_server(
    port: int = typer.Option(
        default=8001, help="The port that the server should listen on. "
    ),
):
    """Starts a Colang Flows actions server."""

    uvicorn.run(actions_server.app, port=port, log_level="info", host="0.0.0.0")
