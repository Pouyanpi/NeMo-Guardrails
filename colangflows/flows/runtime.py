import inspect
import logging
import uuid
from typing import List, Optional

from colangflows.actions.action_dispatcher import ActionDispatcher
from colangflows.actions.actions import ActionResult
from colangflows.actions.fact_checking import check_facts
from colangflows.actions.math import wolfram_alpha_request
from colangflows.actions.jailbreak_check import check_jailbreak
from colangflows.actions.output_moderation import output_moderation
from colangflows.flows.flows import FlowConfig, compute_context, compute_next_steps
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
            "check_facts": check_facts,
            "check_jailbreak": check_jailbreak,
            "output_moderation": output_moderation,
        }

        # Register the actions with the dispatcher.
        self.action_dispatcher = ActionDispatcher(config_path=config.config_path)
        for action_name, action_fn in self.registered_actions.items():
            self.action_dispatcher.register_action(action_fn, action_name)

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
        self.action_dispatcher.register_action(action, name)

    def register_actions(self, actions_obj: any):
        """Registers all the actions from the given object."""
        self.action_dispatcher.register_actions(actions_obj)

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

            # If we need to execute an action, we start doing that.
            if last_event["type"] == "start_action":
                next_events = await self._process_start_action(events)
            else:
                # We need to slide all the flows based on the current event,
                # to compute the next steps.
                next_events = await self.compute_next_steps(events)

                if len(next_events) == 0:
                    next_events = [{"type": "listen"}]

            # Otherwise, we append the event and continue the processing.
            events.extend(next_events)
            new_events.extend(next_events)

            # If the next event is a listen, we stop the processing.
            if next_events[-1]["type"] == "listen":
                break

            # As a safety measure, we stop the processing if we have too many events.
            if len(new_events) > 100:
                raise Exception("Too many events.")

        return new_events

    async def compute_next_steps(self, events: List[dict]) -> List[dict]:
        """Computes the next step based on the current flow."""
        next_steps = compute_next_steps(events, self.flow_configs)

        # If there are any start_action events, we mark if they are system actions or not
        for event in next_steps:
            if event["type"] == "start_action":
                is_system_action = False
                fn = self.action_dispatcher.get_action(event["action_name"])
                if fn:
                    action_meta = getattr(fn, "action_meta", {})
                    is_system_action = action_meta.get("is_system_action", False)
                event["is_system_action"] = is_system_action

        return next_steps

    async def _process_start_action(self, events: List[dict]) -> List[dict]:
        """Starts the specified action, waits for it to finish and posts back the result."""

        event = events[-1]

        action_name = event["action_name"]
        action_params = event["action_params"]
        action_result_key = event["action_result_key"]

        fn = self.action_dispatcher.get_action(action_name)

        if fn is None:
            return [
                {
                    "type": "action_finished",
                    "action_name": action_name,
                    "status": "error",
                    "return_value": "Action not found.",
                }
            ]

        context = compute_context(events)

        action_meta = getattr(fn, "action_meta", {})

        # We pass all the parameters that are passed explicitly to the action.
        kwargs = {**action_params}

        # We also add the "special" parameters.
        parameters = inspect.signature(fn).parameters

        if "events" in parameters:
            kwargs["events"] = events

        if "context" in parameters:
            kwargs["context"] = context
        # Add any additional registered parameters
        for k, v in self.registered_action_params.items():
            if k in parameters:
                kwargs[k] = v

        # If there are parameters which are variables, we replace with actual values.
        for k, v in kwargs.items():
            if isinstance(v, str) and v.startswith("$"):
                var_name = v[1:]
                if var_name in context:
                    kwargs[k] = context[var_name]

        # TODO: here we'll need to call the Actions Server if it is available.
        #  But not for system actions, those should still run locally.
        # result = await fn(**kwargs)
        result, status = await self.action_dispatcher.execute_action(
            action_name, kwargs
        )

        return_value = result
        return_events = []
        context_updates = {}

        if isinstance(result, ActionResult):
            return_value = result.return_value
            return_events = result.events
            context_updates.update(result.context_updates)

        # If we have an action result key, we also record the update.
        if action_result_key:
            context_updates[action_result_key] = return_value

        next_steps = []

        if context_updates:
            next_steps.append({"type": "context_update", "data": context_updates})

        next_steps.append(
            {
                "type": "action_finished",
                "action_name": action_name,
                "action_params": action_params,
                "action_result_key": action_result_key,
                "status": "success",
                "return_value": return_value,
                "events": return_events,
                "is_system_action": action_meta.get("is_system_action", False),
            }
        )

        # If the action returned additional events, we also add them to the next steps.
        if return_events:
            next_steps.extend(return_events)

        return next_steps
