"""Test the flows engine."""
from colangflows.flows.flows import FlowConfig, State, compute_next_state

# Flow configurations for these tests
FLOW_CONFIGS = {
    "greeting": FlowConfig(
        id="greeting",
        elements=[
            {"_type": "user_intent", "intent_name": "express greeting"},
            {
                "_type": "run_action",
                "action_name": "utter",
                "action_params": {"value": "express greeting"},
            },
            {
                "_type": "run_action",
                "action_name": "utter",
                "action_params": {"value": "offer to help"},
            },
        ],
    ),
    "greeting follow up": FlowConfig(
        id="greeting follow up",
        is_extension=True,
        priority=2,
        elements=[
            {
                "_type": "run_action",
                "action_name": "utter",
                "action_params": {"value": "express greeting"},
            },
            {
                "_type": "run_action",
                "action_name": "utter",
                "action_params": {"value": "comment random fact about today"},
            },
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
    assert state.next_step == {
        "_type": "run_action",
        "action_name": "utter",
        "action_params": {"value": "express greeting"},
    }

    state = compute_next_state(
        state,
        {
            "type": "bot_intent",
            "intent": "express greeting",
        },
    )
    assert state.next_step == {
        "_type": "run_action",
        "action_name": "utter",
        "action_params": {"value": "comment random fact about today"},
    }

    state = compute_next_state(
        state,
        {
            "type": "bot_intent",
            "intent": "comment random fact about today",
        },
    )
    assert state.next_step == {
        "_type": "run_action",
        "action_name": "utter",
        "action_params": {"value": "offer to help"},
    }

    state = compute_next_state(
        state,
        {
            "type": "bot_intent",
            "intent": "offer to help",
        },
    )
    assert state.next_step is None
