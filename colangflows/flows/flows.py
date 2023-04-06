"""A simplified modeling of the CoFlows engine."""
import uuid
from dataclasses import dataclass
from enum import Enum
from typing import Dict, List, Optional


@dataclass
class FlowConfig:
    """The configuration of a flow."""

    # A unique id of the flow.
    id: str

    # The sequence of elements that compose the flow.
    elements: List[dict]

    # The priority of the flow. Higher priority flows are executed first.
    priority: float = 1.0

    # Whether it is an extension flow or not.
    # Extension flows can interrupt other flows on actionable steps.
    is_extension: bool = False

    # The events that can trigger this flow to advance.
    trigger_event_types = ["user_intent", "bot_intent", "run_action", "action_finished"]


class FlowStatus(Enum):
    """The status of a flow."""

    ACTIVE = "active"
    INTERRUPTED = "interrupted"
    ABORTED = "aborted"
    COMPLETED = "completed"


@dataclass
class FlowState:
    """The state of a flow."""

    # The unique id of an instance of a flow.
    uid: str

    # The id of the flow.
    flow_id: str

    # The position in the sequence of elements that compose the flow.
    head: int

    # The current state of the flow
    status: FlowStatus = FlowStatus.ACTIVE

    # The UID of the flows that interrupted this one
    interrupted_by = None


@dataclass
class State:
    """A state of a flow-driven system."""

    # The current set of variables in the state.
    context: dict

    # The current set of flows in the state.
    flow_states: List[FlowState]

    # The configuration of all the flows that are available.
    flow_configs: Dict[str, FlowConfig]

    # The next step of the flow-driven system
    next_step: Optional[dict] = None


def _is_actionable(element: dict) -> bool:
    """Checks if the given element is actionable."""
    if element["_type"] == "run_action":
        if (
            element["action_name"] == "utter"
            and element["action_params"]["value"] == "..."
        ):
            return False

        return True

    return False


def _is_match(element: dict, event: dict) -> bool:
    """Checks if the given element matches the given event."""

    # The element type is the first key in the element dictionary
    element_type = element["_type"]

    if event["type"] == "user_intent":
        return element_type == "user_intent" and (
            element["intent_name"] == "..." or element["intent_name"] == event["intent"]
        )

    elif event["type"] == "bot_intent":
        return (
            element_type == "run_action"
            and element["action_name"] == "utter"
            and (
                element["action_params"]["value"] == "..."
                or element["action_params"]["value"] == event["intent"]
            )
        )

    elif event["type"] == "action_finished":
        return (
            element_type == "run_action"
            and element["action_name"] == event["action_name"]
        )

    elif event["type"] == "user_said":
        return element_type == "user_said" and (
            element["content"] == "..." or element["content"] == event["content"]
        )

    elif event["type"] == "bot_said":
        return element_type == "bot_said" and (
            element["content"] == "..." or element["content"] == event["content"]
        )

    return False


def compute_next_state(state: State, event: dict) -> State:
    """Computes the next state of the flow-driven system.

    Currently, this is a very simplified implementation, with the following assumptions:

    - All flows are singleton i.e. you can't have multiple instances of the same flow.
    - Flows can be interrupted by one flow at a time.
    - Flows are resumed when the interruption flow completes.
    - No prioritization between flows, the first one that can decide something will be used.
    """

    # We don't advance flow on `start_action`, but on `action_finished`.
    if event["type"] == "start_action":
        return state

    # We update the context with the new data
    if event["type"] == "context_update":
        # TODO: add support to also remove keys from the context.
        #  maybe with a special context key e.g. "__remove__": ["key1", "key2"]
        state.context.update(event["data"])

    # Initialize the new state
    new_state = State(
        context=state.context, flow_states=[], flow_configs=state.flow_configs
    )

    # The UID of the flow that will determine the next step
    next_step_by_flow_uid = None

    # The priority of the current next step.
    next_step_priority = 0

    # This is to handle an edge case in the simplified implementation
    extension_flow_completed = False

    # First, we try to advance the existing flows
    for flow_state in state.flow_states:
        flow_config = state.flow_configs[flow_state.flow_id]

        # We skip processing any completed/aborted flows
        if (
            flow_state.status == FlowStatus.COMPLETED
            or flow_state.status == FlowStatus.ABORTED
        ):
            continue

        # If it's not a completed flow, we have a valid head element
        flow_head_element = flow_config.elements[flow_state.head]

        # If the flow was interrupted, we just copy it to the new state
        if flow_state.status == FlowStatus.INTERRUPTED:
            new_state.flow_states.append(flow_state)
            continue

        # If the flow is not triggered by the current even type, we copy it as is
        if event["type"] not in flow_config.trigger_event_types:
            new_state.flow_states.append(flow_state)

            # If we don't have a next step up to this point, and the current flow is on
            # an actionable item, we set it as the next step.
            if new_state.next_step is None and _is_actionable(flow_head_element):
                new_state.next_step = flow_head_element
                next_step_by_flow_uid = flow_state.uid

                # Decrease a bit the priority to allow a flow that decides on the current
                # event to take precedence.
                next_step_priority = 0.9 * flow_config.priority
            continue

        if _is_match(flow_config.elements[flow_state.head], event):
            # The flow can advance
            flow_state.head += 1

            new_state.flow_states.append(flow_state)

            # If we did not reach the end of the flow, we add it to the new state
            if flow_state.head < len(flow_config.elements):
                # And if we don't have a next step yet, we set it to the next element
                if (
                    new_state.next_step is None
                    or next_step_priority < flow_config.priority
                ) and _is_actionable(flow_config.elements[flow_state.head]):
                    new_state.next_step = flow_config.elements[flow_state.head]
                    next_step_by_flow_uid = flow_state.uid
                    next_step_priority = flow_config.priority
            else:
                # If a flow finished, we mark it as completed
                flow_state.status = FlowStatus.COMPLETED

                if flow_config.is_extension:
                    extension_flow_completed = True

        # we don't interrupt on executable elements
        elif _is_actionable(flow_config.elements[flow_state.head]):
            flow_state.status = FlowStatus.ABORTED
            new_state.flow_states.append(flow_state)
        else:
            flow_state.status = FlowStatus.INTERRUPTED
            new_state.flow_states.append(flow_state)

    # Next, we try to start new flows
    for flow_config in state.flow_configs.values():
        # If a flow with the same id is started, we skip
        if flow_config.id in [fs.flow_id for fs in new_state.flow_states]:
            continue

        # If the first element matches the current event, we start a new flow
        if _is_match(flow_config.elements[0], event):
            flow_uid = str(uuid.uuid4())
            new_state.flow_states.append(
                FlowState(uid=flow_uid, flow_id=flow_config.id, head=1)
            )

            # And if we don't have a next step yet, we set it to the next element
            flow_head_element = flow_config.elements[1]
            if (
                new_state.next_step is None or next_step_priority < flow_config.priority
            ) and _is_actionable(flow_head_element):
                new_state.next_step = flow_head_element
                next_step_by_flow_uid = flow_uid
                next_step_priority = flow_config.priority

    # If there's any extension flow that has completed, we re-activate all aborted flows
    if extension_flow_completed:
        for flow_state in new_state.flow_states:
            if flow_state.status == FlowStatus.ABORTED:
                flow_state.status = FlowStatus.ACTIVE

                # And potentially use them for the next decision
                flow_config = state.flow_configs[flow_state.flow_id]
                if (
                    new_state.next_step is None
                    or next_step_priority < flow_config.priority
                ) and _is_actionable(flow_config.elements[flow_state.head]):
                    new_state.next_step = flow_config.elements[flow_state.head]
                    next_step_by_flow_uid = flow_state.uid
                    next_step_priority = flow_config.priority

    # If there are any flows that have been interrupted in this interation, we consider
    # them to be interrupted by the flow that determined the next step.
    for flow_state in new_state.flow_states:
        if (
            flow_state.status == FlowStatus.INTERRUPTED
            and flow_state.interrupted_by is None
        ):
            flow_state.interrupted_by = next_step_by_flow_uid

    # We compute the decision flow config and state
    decision_flow_config = None
    for flow_state in new_state.flow_states:
        if flow_state.uid == next_step_by_flow_uid:
            decision_flow_config = state.flow_configs[flow_state.flow_id]

    if decision_flow_config and decision_flow_config.is_extension:
        for flow_state in new_state.flow_states:
            if flow_state.status == FlowStatus.ABORTED:
                flow_state.status = FlowStatus.INTERRUPTED
                flow_state.interrupted_by = next_step_by_flow_uid

    # If there are flows that were waiting on completed flows, we reactivate them
    for flow_state in new_state.flow_states:
        if flow_state.status == FlowStatus.INTERRUPTED:
            # TODO: optimize this with a dict of statuses
            for _flow_state in new_state.flow_states:
                if _flow_state.uid == flow_state.interrupted_by:
                    if _flow_state.status == FlowStatus.COMPLETED:
                        flow_state.status = FlowStatus.ACTIVE
                        flow_state.interrupted_by = []

                        flow_config = state.flow_configs[flow_state.flow_id]
                        # Also, they can be used for decision as well.

                        if (
                            new_state.next_step is None
                            or next_step_priority < flow_config.priority
                        ) and _is_actionable(flow_config.elements[flow_state.head]):
                            new_state.next_step = flow_config.elements[flow_state.head]
                            next_step_by_flow_uid = flow_state.uid
                            next_step_priority = flow_config.priority
                    break

    # If the current event was an "action_finished" with events/context updates attached,
    # the next step is always that creation of that event. The same is true if the return
    # value needs to be saved in a context var.
    if event["type"] == "action_finished" and (
        event.get("events")
        or event.get("context_updates")
        or event.get("action_result_key")
    ):
        new_events = []
        context_updates = {}

        # If we have context updates, we first generate the event for that
        if event.get("context_updates"):
            context_updates.update(event["context_updates"])

        if event.get("action_result_key"):
            context_updates[event["action_result_key"]] = event["return_value"]

        if context_updates:
            new_events.append({"type": "context_update", "data": context_updates})

        # Next, we add the actual events decided by the action
        if event.get("events"):
            new_events.extend(event["events"])

        new_state.next_step = {"_type": "create_events", "events": new_events}

    return new_state


def compute_next_step(
    history: List[dict], flow_configs: Dict[str, FlowConfig]
) -> Optional[dict]:
    """Computes the next step in a flow-driven system given a history of events."""
    state = State(context={}, flow_states=[], flow_configs=flow_configs)

    for event in history:
        state = compute_next_state(state, event)

    return state.next_step


def compute_context(history: List[dict]):
    """Computes the context given a history of events.

    # We also include a few special context variables:
    - $last_user_message: the last message sent by the user.
    - $last_bot_message: the last message sent by the bot.
    """
    context = {
        "last_user_message": None,
        "last_bot_message": None,
    }

    for event in history:
        if event["type"] == "context_update":
            context.update(event["data"])

        if event["type"] == "user_said":
            context["last_user_message"] = event["content"]
        elif event["type"] == "bot_said":
            context["last_bot_message"] = event["content"]

    return context
