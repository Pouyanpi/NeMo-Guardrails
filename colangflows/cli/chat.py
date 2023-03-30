import os
from typing import Optional

from colangflows.rails import LLMRails, RailsConfig

os.environ["TOKENIZERS_PARALLELISM"] = "false"


def run_chat(config_path: Optional[str] = None, verbose: bool = False):
    """Runs a chat session in the terminal."""

    rails_config = RailsConfig.from_path(config_path)

    # TODO: add support for loading a config directly from live playground
    # rails_config = RailsConfig.from_playground(model="...")

    # TODO: add support to register additional actions
    # rails_app.register_action(...)

    rails_app = LLMRails(rails_config, verbose=verbose)

    history = []
    # And go into the default listening loop.
    while True:
        user_message = input("> ")

        history.append({"role": "user", "content": user_message})
        bot_message = rails_app.generate(messages=history)
        history.append(bot_message)

        # We print bot messages in green.
        print(f"\033[92m{bot_message['content']}\033[0m")
