import asyncio
import os
from typing import Optional

from collm.config import RailsConfig
from collm.llmrails import LLMRails

os.environ["TOKENIZERS_PARALLELISM"] = "false"


def run_chat(config_path: Optional[str] = None):
    """Runs a chat session in the terminal."""

    rails_config = RailsConfig.from_path(config_path)
    app = LLMRails(rails_config)

    history = []
    # And go into the default listening loop.
    while True:
        user_message = input("> ")

        history.append({"role": "user", "content": user_message})
        bot_message = asyncio.run(app.generate_async(messages=history))
        history.append(bot_message)

        # We print bot messages in green.
        print(f"\033[92m{bot_message['content']}\033[0m")
