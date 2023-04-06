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
            {"_type": "user_intent", "intent_name": "ask capabilities"},
            {
                "_type": "run_action",
                "action_name": "utter",
                "action_params": {"value": "inform capabilities"},
            },
        ],
    ),
    "benefits": FlowConfig(
        id="benefits",
        elements=[
            {"_type": "user_intent", "intent_name": "ask about benefits"},
            {
                "_type": "run_action",
                "action_name": "utter",
                "action_params": {"value": "respond about benefits"},
            },
            {
                "_type": "run_action",
                "action_name": "utter",
                "action_params": {"value": "ask if user happy"},
            },
        ],
    ),
    "math": FlowConfig(
        id="math",
        elements=[
            {"_type": "user_intent", "intent_name": "ask math question"},
            {"_type": "run_action", "action_name": "wolfram alpha request"},
            {
                "_type": "run_action",
                "action_name": "utter",
                "action_params": {"value": "respond to math question"},
            },
            {
                "_type": "run_action",
                "action_name": "utter",
                "action_params": {"value": "ask if user happy"},
            },
        ],
    ),
}


def test_simple_sequence():
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
    assert state.next_step is None

    state = compute_next_state(
        state,
        {
            "type": "user_intent",
            "intent": "ask capabilities",
        },
    )
    assert state.next_step == {
        "_type": "run_action",
        "action_name": "utter",
        "action_params": {"value": "inform capabilities"},
    }

    state = compute_next_state(
        state,
        {
            "type": "bot_intent",
            "intent": "inform capabilities",
        },
    )
    assert state.next_step is None


def test_not_able_to_start_a_flow():
    """No flow should be able to start."""
    state = State(context={}, flow_states=[], flow_configs=FLOW_CONFIGS)

    state = compute_next_state(
        state,
        {
            "type": "user_intent",
            "intent": "ask capabilities",
        },
    )
    assert state.next_step is None


def test_two_consecutive_bot_messages():
    """Test a sequence of two bot messages."""
    state = State(context={}, flow_states=[], flow_configs=FLOW_CONFIGS)

    state = compute_next_state(
        state,
        {
            "type": "user_intent",
            "intent": "ask about benefits",
        },
    )
    assert state.next_step == {
        "_type": "run_action",
        "action_name": "utter",
        "action_params": {"value": "respond about benefits"},
    }

    state = compute_next_state(
        state,
        {
            "type": "bot_intent",
            "intent": "respond about benefits",
        },
    )
    assert state.next_step == {
        "_type": "run_action",
        "action_name": "utter",
        "action_params": {"value": "ask if user happy"},
    }

    state = compute_next_state(
        state,
        {
            "type": "bot_intent",
            "intent": "ask if user happy",
        },
    )
    assert state.next_step is None


def test_action_execution():
    """Test a sequence of with an action execution."""
    state = State(context={}, flow_states=[], flow_configs=FLOW_CONFIGS)

    state = compute_next_state(
        state,
        {
            "type": "user_intent",
            "intent": "ask math question",
        },
    )
    assert state.next_step == {
        "_type": "run_action",
        "action_name": "wolfram alpha request",
    }

    state = compute_next_state(
        state,
        {
            "type": "action_finished",
            "action_name": "wolfram alpha request",
        },
    )
    assert state.next_step == {
        "_type": "run_action",
        "action_name": "utter",
        "action_params": {"value": "respond to math question"},
    }

    state = compute_next_state(
        state,
        {
            "type": "bot_intent",
            "intent": "respond to math question",
        },
    )
    assert state.next_step == {
        "_type": "run_action",
        "action_name": "utter",
        "action_params": {"value": "ask if user happy"},
    }

    state = compute_next_state(
        state,
        {
            "type": "bot_intent",
            "intent": "ask if user happy",
        },
    )
    assert state.next_step is None


def test_flow_interruption():
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
    assert state.next_step is None

    state = compute_next_state(
        state,
        {
            "type": "user_intent",
            "intent": "ask about benefits",
        },
    )
    assert state.next_step == {
        "_type": "run_action",
        "action_name": "utter",
        "action_params": {"value": "respond about benefits"},
    }

    state = compute_next_state(
        state,
        {
            "type": "bot_intent",
            "intent": "respond about benefits",
        },
    )
    assert state.next_step == {
        "_type": "run_action",
        "action_name": "utter",
        "action_params": {"value": "ask if user happy"},
    }

    state = compute_next_state(
        state,
        {
            "type": "bot_intent",
            "intent": "ask if user happy",
        },
    )
    assert state.next_step is None

    state = compute_next_state(
        state,
        {
            "type": "user_intent",
            "intent": "ask capabilities",
        },
    )
    assert state.next_step == {
        "_type": "run_action",
        "action_name": "utter",
        "action_params": {"value": "inform capabilities"},
    }

    state = compute_next_state(
        state,
        {
            "type": "bot_intent",
            "intent": "inform capabilities",
        },
    )
    assert state.next_step is None
