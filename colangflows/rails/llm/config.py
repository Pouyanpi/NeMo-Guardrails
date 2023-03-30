"""Module for the configuration of rails."""
import os
from typing import Dict, List, Optional

import yaml
from pydantic import BaseModel
from pydantic.fields import Field

from colangflows.language.parser import parse_colang_file


class Model(BaseModel):
    """Configuration of a model used by the rails engine.

    Typically, the main model is configured e.g.:
    {
        "type": "main",
        "engine": "nemollm",
        "model": "gpt8b"
    }
    """

    type: str
    engine: str
    model: str


class Instruction(BaseModel):
    """Configuration for instructions in natural language that should be passed to the LLM."""

    type: str
    content: str


class RailsConfig(BaseModel):
    """Configuration object for the models and the rails.

    TODO: add typed config for user_messages, bot_messages, and flows.
    """

    models: List[Model] = Field(
        description="The list of models used by the rails configuration."
    )

    user_messages: Dict[str, List[str]] = Field(
        default_factory=dict,
        description="The list of user messages that should be used for the rails.",
    )

    bot_messages: Dict[str, List[str]] = Field(
        default_factory=dict,
        description="The list of bot messages that should be used for the rails.",
    )

    flows: List[Dict] = Field(
        default_factory=list,
        description="The list of flows that should be used for the rails.",
    )

    instructions: Optional[List[Instruction]] = Field(
        default=None,
        description="List of instructions in natural language that the LLM should use.",
    )

    @staticmethod
    def from_path(config_path: str):
        """Loads a configuration from a given path.

        Supports loading a from a single file, or from a directory.
        """
        # If the config path is a file, we load the YAML content.
        # Otherwise, if it's a folder, we iterate through all files.
        if config_path.endswith(".yaml") or config_path.endswith(".yml"):
            with open(config_path) as f:
                raw_config = yaml.safe_load(f.read())
        elif os.path.isdir(config_path):
            # Iterate all .yml files and join them
            raw_config = {}
            for file in os.listdir(config_path):
                if (
                    not file.endswith(".yaml")
                    and not file.endswith(".yml")
                    and not file.endswith(".co")
                ):
                    continue

                # Extract the full path for the file
                full_path = os.path.join(config_path, file)

                if file.endswith(".yml") or file.endswith(".yaml"):
                    with open(full_path) as f:
                        _raw_config = yaml.safe_load(f.read())
                elif file.endswith(".co"):
                    with open(full_path) as f:
                        _raw_config = parse_colang_file(file, content=f.read())

                # We join _raw_config with raw_config.
                # For the keys `user_messages` and `bot_messages` we merge the dictionaries.
                # For the key `flows` and `models` we merge the lists.
                raw_config["user_messages"] = {
                    **raw_config.get("user_messages", {}),
                    **_raw_config.get("user_messages", {}),
                }

                raw_config["bot_messages"] = {
                    **raw_config.get("bot_messages", {}),
                    **_raw_config.get("bot_messages", {}),
                }

                raw_config["instructions"] = raw_config.get(
                    "instructions", []
                ) + _raw_config.get("instructions", [])

                raw_config["flows"] = raw_config.get("flows", []) + _raw_config.get(
                    "flows", []
                )
                raw_config["models"] = raw_config.get("models", []) + _raw_config.get(
                    "models", []
                )
        else:
            raise Exception(f"Invalid config path {config_path}.")

        return RailsConfig.parse_obj(raw_config)
