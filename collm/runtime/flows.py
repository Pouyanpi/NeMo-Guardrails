"""A simplified modeling of the CoFlows engine."""
import uuid
from dataclasses import dataclass
from typing import Dict, List, Optional


@dataclass
class FlowConfig:
    """The configuration of a flow."""

    # A unique id of the flow.
    id: str

    # The sequence of elements that compose the flow.
    elements: List[dict]


@dataclass
class FlowState:
    """The state of a flow."""

    # The unique id of an instance of a flow.
    uid: str

    # The id of the flow.
    flow_id: str

    # The position in the sequence of elements that compose the flow.
    head: int


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
    return ("bot" in element and element["bot"] != "...") or "execute" in element


def _is_match(element: dict, event: dict) -> bool:
    """Checks if the given element matches the given event."""

    # The element type is the first key in the element dictionary
    element_type = list(element.keys())[0]

    if event["type"] == "user_intent":
        return element_type == "user" and (
            element["user"] == "..." or element["user"] == event["intent"]
        )

    elif event["type"] == "bot_intent":
        return element_type == "bot" and (
            element["bot"] == "..." or element["bot"] == event["intent"]
        )

    elif event["type"] == "action_finished":
        return element_type == "execute" and element["execute"] == event["action_name"]

    return False


def compute_next_state(state: State, event: dict) -> State:
    """Computes the next state of the flow-driven system.

    Currently, this is a very simplified implementation, with the following assumptions:

    - All flows are singleton i.e. you can't have multiple instances of the same flow.
    - Flows cannot be interrupted, i.e. if they can't continue, they get aborted.
    - No prioritization between flows, the first one that can decide something will be used.
    """
    # Currently, no flows advance on user_said or bot_said, so we just ignore.
    if event["type"] in ("user_said", "bot_said"):
        return state

    # We don't advance flow on `start_action`, but on `action_finished`.
    if event["type"] == "start_action":
        return state

    # Initialize the new state
    new_state = State(
        context=state.context, flow_states=[], flow_configs=state.flow_configs
    )

    # First, we try to advance the existing flows
    for flow_state in state.flow_states:
        flow_config = state.flow_configs[flow_state.flow_id]
        if _is_match(flow_config.elements[flow_state.head], event):
            # The flow can advance
            flow_state.head += 1

            # If we did not reach the end of the flow, we add it to the new state
            if flow_state.head < len(flow_config.elements):
                new_state.flow_states.append(flow_state)

                # And if we don't have a next step yet, we set it to the next element
                head_element = flow_config.elements[flow_state.head]
                if new_state.next_step is None and _is_actionable(head_element):
                    new_state.next_step = head_element

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
            head_element = flow_config.elements[1]
            if new_state.next_step is None and _is_actionable(head_element):
                new_state.next_step = head_element

    return new_state


def compute_next_step(
    history: List[dict], flow_configs: Dict[str, FlowConfig]
) -> Optional[dict]:
    """Computes the next step in a flow-driven system given a history of events."""
    state = State(context={}, flow_states=[], flow_configs=flow_configs)

    for event in history:
        state = compute_next_state(state, event)

    return state.next_step
