"""LLM Rails entry point."""
import asyncio
import logging
import os
from typing import List, Optional

import yaml
from langchain.llms import BaseLLM, OpenAI

from colangflows.actions.llm.generation import LLMGenerationActions
from colangflows.actions.llm.utils import get_colang_history
from colangflows.flows.runtime import Runtime
from colangflows.language.coyml_parser import parse_flow_elements
from colangflows.llm.nemollm import NeMoLLM
from colangflows.rails.llm.config import RailsConfig
from colangflows.rails.llm.utils import get_history_cache_key

log = logging.getLogger(__name__)


class LLMRails:
    """Rails based on a given configuration."""

    def __init__(
        self, config: RailsConfig, llm: Optional[BaseLLM] = None, verbose: bool = False
    ):
        self.config = config
        self.llm = llm
        self.verbose = verbose

        # We keep a cache of the events history associated with a sequence of user messages.
        # TODO: when we update the interface to allow to return a "state object", this
        #   should be removed
        self.events_history_cache = {}

        # We also load the default flows from the `default_flows.yml` file in the current folder.
        current_folder = os.path.dirname(__file__)
        default_flows_path = os.path.join(current_folder, "llm_flows.yml")
        with open(default_flows_path, "r") as f:
            default_flows = yaml.safe_load(f)["flows"]
            for flow_data in default_flows:
                if flow_data.get("elements") and not flow_data["elements"][0].get(
                    "_type"
                ):
                    flow_data["elements"] = parse_flow_elements(flow_data["elements"])

        # We add the default flows to the config.
        self.config.flows.extend(default_flows)

        # First, we initialize the runtime.
        self.runtime = Runtime(config=config, verbose=verbose)

        # Next, we initialize the LLM engine.
        self._init_llm()
        self.runtime.register_action_param("llm", self.llm)

        # Next, we initialize the LLM Generate actions and register them.
        actions = LLMGenerationActions(config=config, llm=self.llm, verbose=verbose)
        self.runtime.register_actions(actions)

    def _init_llm(self):
        """Initializes the right LLM engine based on the configuration."""

        # If we already have a pre-configured one, we do nothing.
        if self.llm is not None:
            return

        # TODO: Currently we assume the first model is the main one. Add proper support
        #  to search for the main model config.
        main_llm_config = self.config.models[0]

        if main_llm_config.engine == "openai":
            self.llm = OpenAI(model_name=main_llm_config.model, temperature=0.1)

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
        cache_key = get_history_cache_key(messages, include_last=False)
        events = self.events_history_cache.get(cache_key, []).copy()

        events.append({"type": "user_said", "content": messages[-1]["content"]})

        new_events = await self.runtime.generate_events(events)

        # Save the new events in the history and update the cache
        events.extend(new_events)
        cache_key = get_history_cache_key(messages, include_last=True)
        self.events_history_cache[cache_key] = events

        # Extract and join all the messages from bot_said events as the response.
        responses = []
        for event in new_events:
            if event["type"] == "bot_said":
                # Check if we need to remove a message
                if event["content"] == "(remove last message)":
                    responses = responses[0:-1]
                else:
                    responses.append(event["content"])

        # If logging is enabled, we log the conversation
        # TODO: add support for logging flag
        if self.verbose:
            history = get_colang_history(events)
            log.info(f"Conversation history so far: \n{history}")

        return {"role": "assistant", "content": "\n".join(responses)}

    def generate(
        self, prompt: Optional[str] = None, messages: Optional[List[dict]] = None
    ):
        """Synchronous version of generate_async."""
        return asyncio.run(self.generate_async(prompt=prompt, messages=messages))

    def register_action(self, action: callable, name: Optional[str] = None):
        """Register a custom action for the rails configuration."""
        self.runtime.register_action(action, name)
