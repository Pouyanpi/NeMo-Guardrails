import inspect
import logging
import uuid
from typing import List, Optional

from colangflows.actions.actions import ActionResult
from colangflows.actions.fact_checking import check_facts
from colangflows.actions.math import wolfram_alpha_request
from colangflows.flows.flows import FlowConfig, compute_context, compute_next_step
from colangflows.rails.llm.config import RailsConfig

log = logging.getLogger(__name__)


class Runtime:
    """Runtime for executing the Colang flows."""

    def __init__(self, config: RailsConfig, verbose: bool = False):
        self.config = config
        self.verbose = verbose

        # The dictionary of registered actions, initialized with default ones.
        self.registered_actions = {
            "wolfram alpha request": wolfram_alpha_request,
            "check facts": check_facts,
        }

        # The list of additional parameters that can be passed to the actions.
        self.registered_action_params = {}

        self._init_flow_configs()

    def _init_flow_configs(self):
        """Initializes the flow configs based on the config."""
        self.flow_configs = {}

        for flow in self.config.flows:
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

    def register_action(self, action: callable, name: Optional[str] = None):
        """Registers an action with the given name.

        :param name: The name of the action.
        :param action: The action function.
        """
        if name is None:
            action_meta = getattr(action, "action_meta", None)
            name = action_meta["name"] if action_meta else action.__name__

        self.registered_actions[name] = action

    def register_actions(self, actions_obj: any):
        """Registers all the actions from the given object."""
        # Register the actions
        for attr in dir(actions_obj):
            val = getattr(actions_obj, attr)

            if hasattr(val, "action_meta"):
                self.register_action(val)

    def register_action_param(self, name: str, value: any):
        """Registers an additional parameter that can be passed to the actions.

        :param name: The name of the parameter.
        :param value: The value of the parameter.
        """
        self.registered_action_params[name] = value

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

            next_events = None

            # If we need to execute an action, we start doing that.
            if last_event["type"] == "start_action":
                next_events = [await self._process_start_action(events)]
            else:
                # We need to slide all the flows based on the current event,
                # to compute the next step.
                next_step = await self.compute_next_step(events)

                if next_step:
                    next_step_type = list(next_step.keys())[0]

                    if next_step_type == "bot":
                        next_events = [
                            {"type": "bot_intent", "intent": next_step["bot"]}
                        ]

                    elif next_step_type == "execute":
                        action_name = next_step["execute"]
                        is_system_action = False
                        fn = self.registered_actions.get(action_name)
                        if fn:
                            action_meta = getattr(fn, "action_meta", {})
                            is_system_action = action_meta.get(
                                "is_system_action", False
                            )

                        next_events = [
                            {
                                "type": "start_action",
                                "is_system_action": is_system_action,
                                "action_name": next_step["execute"],
                            }
                        ]

                    elif next_step_type == "create_events":
                        next_events = next_step["create_events"]

                else:
                    next_events = [{"type": "listen"}]

            # Otherwise, we append the event and continue the processing.
            events.extend(next_events)
            new_events.extend(next_events)

            # If the next event is a listen, we stop the processing.
            if next_events[-1]["type"] == "listen":
                break

        return new_events

    async def compute_next_step(self, events: List[dict]) -> dict:
        """Computes the next step based on the current flow."""
        next_step = compute_next_step(events, self.flow_configs)

        return next_step

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
        context = compute_context(events)

        fn = self.registered_actions[action_name]
        action_meta = getattr(fn, "action_meta", {})

        # We only pass the parameters that are required
        kwargs = {}

        parameters = inspect.signature(fn).parameters
        if "events" in parameters:
            kwargs["events"] = events

        if "context" in parameters:
            kwargs["context"] = context

        # Add any additional registered parameters
        for k, v in self.registered_action_params.items():
            if k in parameters:
                kwargs[k] = v

        # TODO: here we'll need to call the Actions Server if it is available.
        result = await fn(**kwargs)

        return_value = result
        return_events = []
        context_updates = None

        if isinstance(result, ActionResult):
            return_value = result.return_value
            return_events = result.events
            context_updates = result.context_updates

        return {
            "type": "action_finished",
            "action_name": action_name,
            "status": "success",
            "return_value": return_value,
            "events": return_events,
            "context_updates": context_updates,
            "is_system_action": action_meta.get("is_system_action", False),
        }
