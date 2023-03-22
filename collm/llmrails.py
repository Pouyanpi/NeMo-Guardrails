"""LLM Rails entry point."""
import asyncio
import logging
from typing import List, Optional

from langchain.llms import OpenAI

from collm.config import RailsConfig
from collm.llms.nemollm import NeMoLLM
from collm.runtime.runtime import Runtime

log = logging.getLogger(__name__)


class LLMRails:
    """Rails based on a given configuration."""

    def __init__(self, config: RailsConfig, verbose: bool = False):
        self.config = config

        # First, we initialize the LLM engine.
        self._init_llm()

        # Next, the runtime.
        self.runtime = Runtime(config=config, llm=self.llm, verbose=verbose)

        # NOTE: we currently keep an explicit history of events per LLMRails instance.
        # This means this instance can only be used for one conversation.
        # Once support for returning the history of events, and passing this back, will be
        # added, we can remove this.
        self.events = []

    def _init_llm(self):
        """Initializes the right LLM engine based on the configuration."""
        self.llm = None

        # TODO: Currently we assume the first model is the main one. Add proper support
        #  to search for the main model config.
        main_llm_config = self.config.models[0]

        if main_llm_config.engine == "openai":
            self.llm = OpenAI(model_name=main_llm_config.model)

        elif main_llm_config.engine == "nemollm":
            self.llm = NeMoLLM(model=main_llm_config.model)

    async def generate_async(
        self, prompt: Optional[str] = None, messages: Optional[List[dict]] = None
    ):
        """Generates a completion or a next message.

        The format for messages is currently the following:
        [
            {"role": "user", "content": "Hello! How are you?"},
            {"role": "assistant", "content": "I am fine, thank you!"},
        ]
        System messages are not yet supported.

        """
        if prompt is not None:
            raise Exception("Prompt is not supported yet.")

        # TODO: Add support to load back history of events, next to history of messages
        #   This is important as without it, the LLM prediction is not as good.

        # First, we turn the messages into a history of events.
        # events = []
        # for message in messages:
        #     if message.get("role") == "user":
        #         events.append({"type": "user_said", "content": message["content"]})
        #     elif message.get("role") == "assistant":
        #         events.append({"type": "bot_said", "content": message["content"]})

        self.events.append({"type": "user_said", "content": messages[-1]["content"]})

        responses = []
        while True:
            event = await self.runtime.process_events(self.events)
            if event["type"] == "listen":
                break

            elif event["type"] == "bot_said":
                responses.append(event["content"])
                self.events.append(event)

            # We just loop back in these internal events
            elif event["type"] in [
                "user_intent",
                "bot_intent",
                "start_action",
                "action_finished",
            ]:
                self.events.append(event)
            else:
                raise Exception("Unsupported event type: " + event["type"])

        return {"role": "assistant", "content": "\n".join(responses)}

    def generate(
        self, prompt: Optional[str] = None, messages: Optional[List[dict]] = None
    ):
        """Synchronous version of generate_async."""
        return asyncio.run(self.generate_async(prompt=prompt, messages=messages))
