"""Test the flows engine."""
from collm.runtime.flows import FlowConfig, State, compute_next_state

# Flow configurations for these tests
FLOW_CONFIGS = {
    "greeting": FlowConfig(
        id="greeting",
        elements=[
            {"user": "express greeting"},
            {"bot": "express greeting"},
            {"bot": "offer to help"},
        ],
    ),
    "greeting follow up": FlowConfig(
        id="greeting follow up",
        is_extension=True,
        priority=2,
        elements=[
            {"bot": "express greeting"},
            {"bot": "comment random fact about today"},
        ],
    ),
}


def test_extension_flows_1():
    """Test a simple sequence of two turns in a flow."""
    state = State(context={}, flow_states=[], flow_configs=FLOW_CONFIGS)

    state = compute_next_state(
        state,
        {
            "type": "user_intent",
            "intent": "express greeting",
        },
    )
    assert state.next_step == {"bot": "express greeting"}

    state = compute_next_state(
        state,
        {
            "type": "bot_intent",
            "intent": "express greeting",
        },
    )
    assert state.next_step == {"bot": "comment random fact about today"}

    state = compute_next_state(
        state,
        {
            "type": "bot_intent",
            "intent": "comment random fact about today",
        },
    )
    assert state.next_step == {"bot": "offer to help"}

    state = compute_next_state(
        state,
        {
            "type": "bot_intent",
            "intent": "offer to help",
        },
    )
    assert state.next_step is None
