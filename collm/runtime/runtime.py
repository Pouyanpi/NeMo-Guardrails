import inspect
import json
import logging
import os
import random
import uuid
from typing import List

import yaml
from langchain import LLMChain, PromptTemplate
from langchain.llms import BaseLLM

from collm.actions.actions import ActionResult
from collm.actions.fact_checking import check_facts
from collm.actions.math import wolfram_alpha_request
from collm.config import RailsConfig
from collm.kb.basic import BasicEmbeddingsIndex
from collm.kb.index import IndexItem
from collm.prompts.prompts import Step, get_prompt
from collm.runtime.flows import FlowConfig, compute_next_step
from collm.runtime.utils import flow_to_colang, get_colang_history

log = logging.getLogger(__name__)

SYSTEM_ACTIONS = [
    "generate_user_intent",
    "generate_next_step",
    "generate_bot_message",
]


class Runtime:
    """Runtime for executing the CoLLM flows."""

    def __init__(self, config: RailsConfig, llm: BaseLLM, verbose: bool = False):
        self.config = config
        self.llm = llm
        self.verbose = verbose

        # If we have user messages, we build an index with them
        self.user_message_index = None
        self._init_user_message_index()

        self.bot_message_index = None
        self._init_bot_message_index()

        self.flows_index = None
        self._init_flows_index()

        # The dictionary of registered actions, initialized with default ones.
        self.registered_actions = {
            "wolfram alpha request": wolfram_alpha_request,
            "check facts": check_facts,
        }

        self._init_flow_configs()

    def _init_flow_configs(self):
        """Initializes the flow configs based on the config."""
        self.flow_configs = {}

        # We also load the default flows from the `default_flows.yml` file in the current folder.
        current_folder = os.path.dirname(__file__)
        default_flows_path = os.path.join(current_folder, "default_flows.yml")
        with open(default_flows_path, "r") as f:
            default_flows = yaml.safe_load(f)["flows"]

        for flow in self.config.flows + default_flows:
            elements = flow["elements"]

            # If we don't have an id, we generate a random UID.
            flow_id = flow.get("id") or str(uuid.uuid4())

            self.flow_configs[flow_id] = FlowConfig(
                id=flow_id,
                elements=elements,
                priority=flow.get("priority", 1.0),
                is_extension=flow.get("is_extension", False),
            )

            # We also compute what types of events can trigger this flow, in addition
            # to the default ones.
            for element in elements:
                if element.get("user_said"):
                    self.flow_configs[flow_id].trigger_event_types.append("user_said")

    def _init_user_message_index(self):
        """Initializes the index of user messages."""

        if not self.config.user_messages:
            return

        items = []
        for intent, utterances in self.config.user_messages.items():
            for text in utterances:
                items.append(IndexItem(text=text, meta={"intent": intent}))

        # If we have no patterns, we stop.
        if len(items) == 0:
            return

        self.user_message_index = BasicEmbeddingsIndex()
        self.user_message_index.add_items(items)

        # NOTE: this should be very fast, otherwise needs to be moved to separate thread.
        self.user_message_index.build()

    def _init_bot_message_index(self):
        """Initializes the index of bot messages."""

        if not self.config.bot_messages:
            return

        items = []
        for intent, utterances in self.config.bot_messages.items():
            for text in utterances:
                items.append(IndexItem(text=intent, meta={"text": text}))

        # If we have no patterns, we stop.
        if len(items) == 0:
            return

        self.bot_message_index = BasicEmbeddingsIndex()
        self.bot_message_index.add_items(items)

        # NOTE: this should be very fast, otherwise needs to be moved to separate thread.
        self.bot_message_index.build()

    def _init_flows_index(self):
        """Initializes the index of flows."""

        if not self.config.flows:
            return

        items = []
        for flow in self.config.flows:
            colang_flow = flow_to_colang(flow)

            # We index on the full body for now
            items.append(IndexItem(text=colang_flow, meta={"flow": colang_flow}))

        # If we have no patterns, we stop.
        if len(items) == 0:
            return

        self.flows_index = BasicEmbeddingsIndex()
        self.flows_index.add_items(items)

        # NOTE: this should be very fast, otherwise needs to be moved to separate thread.
        self.flows_index.build()

    def register_action(self, name: str, action: callable):
        """Registers an action with the given name.

        :param name: The name of the action.
        :param action: The action function.
        """
        self.registered_actions[name] = action

    async def generate_events(self, events: List[dict]) -> List[dict]:
        """Generates the next events based on the provided history.

        This is a wrapper around the `process_events` method, that will keep
        processing the events until the `listen` event is produced.

        :return: The list of events.
        """
        events = events.copy()
        new_events = []

        while True:
            last_event = events[-1]

            log.info("Processing event: %s", last_event)

            # print the array of events in JSON format
            # print(f"\033[91m{json.dumps(events, indent=True)}\033[0m")

            next_event = None

            # If we need to execute an action, we start doing that.
            if last_event["type"] == "start_action":
                action_name = last_event["action_name"]
                action_result = None

                # If it's a system action, we invoke the special actions
                # TODO: normalize this even further and register this with the runtime
                #   in a cleaner way.
                if action_name in SYSTEM_ACTIONS:
                    if action_name == "generate_user_intent":
                        action_result = await self._generate_user_intent(events)
                    elif action_name == "generate_next_step":
                        action_result = await self._generate_next_step(events)
                    elif action_name == "generate_bot_message":
                        action_result = await self._generate_bot_message(events)

                    # We first add the action finished event, and then the
                    next_event = {
                        "type": "action_finished",
                        "action_name": action_name,
                        "status": "success",
                        "return_value": action_result.return_value,
                        "events": action_result.events,
                        "system": True,
                    }
                else:
                    # Otherwise, we process it the normal way.
                    next_event = await self._process_start_action(events)
            else:
                # We need to slide all the flows based on the current event,
                # to compute the next step.
                next_step = await self.compute_next_step(events)

                if next_step:
                    next_step_type = list(next_step.keys())[0]

                    if next_step_type == "bot":
                        next_event = {"type": "bot_intent", "intent": next_step["bot"]}

                    elif next_step_type == "execute":
                        next_event = {
                            "type": "start_action",
                            "system": next_step["execute"] in SYSTEM_ACTIONS,
                            "action_name": next_step["execute"],
                        }

                    elif next_step_type == "create_event":
                        next_event = next_step["create_event"]

                else:
                    next_event = {"type": "listen"}

            # Otherwise, we append the event and continue the processing.
            events.append(next_event)
            new_events.append(next_event)

            # If the next event is a listen, we stop the processing.
            if next_event["type"] == "listen":
                break

        return new_events

    async def compute_next_step(self, events: List[dict]) -> dict:
        """Computes the next step based on the current flow."""
        next_step = compute_next_step(events, self.flow_configs)

        return next_step

    async def _generate_user_intent(self, events: List[dict]):
        """Processes the user_said event."""

        # The last event should be the "start_action" and the one before it the "user_said".
        event = events[-2]
        assert event["type"] == "user_said"

        # TODO: check for an explicit way of enabling the canonical form detection

        if self.config.user_messages:
            # TODO: based on the config we can use a specific canonical forms model
            #  or use the LLM to detect the canonical form. The below implementation
            #  is for the latter.

            # Compute the conversation history
            history = get_colang_history(events)

            # We search for the most relevant similar user utterance
            examples = ""
            if self.user_message_index:
                results = self.user_message_index.search(
                    text=event["content"], max_results=5
                )

                # We add these in reverse order so the most relevant is towards the end.
                for result in reversed(results):
                    examples += f"user \"{result.text}\"\n  {result.meta['intent']}\n\n"

            # We have user messages, so we need to identify the canonical form.
            canonical_form_prompt = PromptTemplate(
                input_variables=["history", "examples"],
                template=get_prompt(
                    self.config, Step.DETECT_USER_MESSAGE_CANONICAL_FORM
                )["content"],
            )

            # Create and run the general chain.
            chain = LLMChain(
                prompt=canonical_form_prompt, llm=self.llm, verbose=self.verbose
            )
            result = await chain.apredict(history=history, examples=examples)
            if result[0] == "\n":
                result = result[1:]
            result = result.split("\n")[0].strip()
            user_intent = result

            log.info("Canonical form for user intent: " + user_intent)

            return ActionResult(events=[{"type": "user_intent", "intent": user_intent}])
        else:
            # This is the pass-through behavior.
            # First, we compute the general instructions.
            instruction_items = []
            if self.config.instructions:
                for instruction in self.config.instructions:
                    instruction_items.append(instruction.content)
            general_instructions = "\n".join(instruction_items)

            # Next, we compute the history from all the messages
            history_items = []
            for event in events:
                if event["type"] == "user_said":
                    history_items.append("User: " + event["content"])
                elif event["type"] == "bot_said":
                    history_items.append("Assistant: " + event["content"])
            history = "\n".join(history_items)

            general_prompt = PromptTemplate(
                input_variables=["general_instructions", "history"],
                template=get_prompt(self.config, Step.GENERAL)["content"],
            )

            # Create and run the general chain.
            chain = LLMChain(prompt=general_prompt, llm=self.llm, verbose=self.verbose)

            result = await chain.apredict(
                general_instructions=general_instructions,
                history=history,
                stop=["User: "],
            )

            return ActionResult(
                events=[{"type": "bot_said", "content": result.strip()}]
            )

    async def _generate_next_step(self, events: List[dict]):
        # The last event should be the "start_action" and the one before it the "user_intent".
        event = events[-2]

        # Currently, we only predict next step after a user intent using LLM
        if event["type"] == "user_intent":
            user_intent = event["intent"]

            # We use the LLM to predict the next step
            # Compute the conversation history
            history = get_colang_history(events, include_texts=False)

            # We search for the most relevant similar user utterance
            examples = ""
            if self.flows_index:
                results = self.flows_index.search(text=user_intent, max_results=5)

                # We add these in reverse order so the most relevant is towards the end.
                for result in reversed(results):
                    examples += f"{result.text}\n"

            predict_next_step_prompt = PromptTemplate(
                input_variables=["history", "examples"],
                template=get_prompt(self.config, Step.PREDICT_NEXT_STEP)["content"],
            )

            # Create and run the general chain.
            chain = LLMChain(
                prompt=predict_next_step_prompt, llm=self.llm, verbose=self.verbose
            )
            result = await chain.apredict(history=history, examples=examples)
            if result[0] == "\n":
                result = result[1:]
            result = result.split("\n")[0].strip()

            if result.startswith("bot "):
                next_step = {"bot": result[4:]}
            else:
                next_step = {"bot": "general response"}

            # If we have to execute an action, we return the event to start it
            if next_step.get("execute"):
                return ActionResult(
                    events=[
                        {"type": "start_action", "action_name": next_step["execute"]}
                    ]
                )
            else:
                bot_intent = next_step.get("bot")

                return ActionResult(
                    events=[{"type": "bot_intent", "intent": bot_intent}]
                )

        return ActionResult(return_value=None)

    async def _generate_bot_message(self, events: List[dict]):
        # The last event should be the "start_action" and the one before it the "bot_intent".
        event = events[-2]
        assert event["type"] == "bot_intent"

        bot_intent = event["intent"]

        if bot_intent in self.config.bot_messages:
            # Choose a message randomly from self.config.bot_messages[bot_message]
            bot_utterance = random.choice(self.config.bot_messages[bot_intent])

            log.info("Found existing bot message: " + bot_utterance)
        else:
            history = get_colang_history(events)

            # We search for the most relevant similar bot utterance
            examples = ""
            if self.bot_message_index:
                results = self.bot_message_index.search(
                    text=event["intent"], max_results=5
                )

                # We add these in reverse order so the most relevant is towards the end.
                for result in reversed(results):
                    examples += f"bot {result.text}\n  \"{result.meta['text']}\"\n\n"

            # Otherwise, we generate a message with the LLM
            bot_message_prompt = PromptTemplate(
                input_variables=["history", "examples"],
                template=get_prompt(self.config, Step.GENERATE_BOT_MESSAGE)["content"],
            )

            chain = LLMChain(
                prompt=bot_message_prompt, llm=self.llm, verbose=self.verbose
            )
            result = await chain.apredict(history=history, examples=examples)
            if result[0] == "\n":
                result = result[1:]
            result = result.split("\n")[0].strip()

            # Strip the quotes
            if result[0] == '"':
                result = result[1:-1]

            bot_utterance = result

            log.info("Generated bot message: " + bot_utterance)

        return ActionResult(events=[{"type": "bot_said", "content": bot_utterance}])

    async def _process_start_action(self, events: List[dict]):
        """Starts the specified action, waits for it to finish and posts back the result."""

        event = events[-1]

        action_name = event["action_name"]
        if action_name not in self.registered_actions:
            return {
                "type": "action_finished",
                "action_name": action_name,
                "status": "error",
                "return_value": "Action not found.",
            }

        # TODO: pass parameters and context
        context = {}

        # Quick hack to add the last user message
        context["last_user_message"] = None
        context["last_bot_message"] = None

        i = len(events) - 1
        while i >= 0:
            if (
                events[i]["type"] == "user_said"
                and context["last_user_message"] is None
            ):
                context["last_user_message"] = events[i]["content"]

            if events[i]["type"] == "bot_said" and context["last_bot_message"] is None:
                context["last_bot_message"] = events[i]["content"]

            i -= 1

        kwargs = {"context": context}
        fn = self.registered_actions[action_name]

        # Check if fn has a parameter called "runtime"
        if "runtime" in inspect.signature(fn).parameters:
            kwargs["runtime"] = self

        result = await self.registered_actions[action_name](**kwargs)

        return_value = result
        events = []

        if isinstance(result, ActionResult):
            return_value = result.return_value
            events = result.events

        return {
            "type": "action_finished",
            "action_name": action_name,
            "status": "success",
            "return_value": return_value,
            "events": events,
        }
