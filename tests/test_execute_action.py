import os

import pytest

from colangflows.rails import LLMRails, RailsConfig
from tests.utils import FakeLLM

TEST_CONFIGS_PATH = os.path.join(os.path.dirname(__file__), "test_configs")


@pytest.fixture
def rails_config():
    return RailsConfig.from_path(os.path.join(TEST_CONFIGS_PATH, "simple_actions"))


@pytest.mark.asyncio
async def test_action_execution_with_result(rails_config):
    llm = FakeLLM(
        responses=[
            "  express greeting",
        ]
    )

    llm_rails = LLMRails(config=rails_config, llm=llm)

    async def fetch_profile():
        return {
            "name": "John",
        }

    llm_rails.runtime.register_action(fetch_profile)

    events = [{"type": "user_said", "content": "Hello!"}]

    new_events = await llm_rails.runtime.generate_events(events)

    assert new_events == [
        {
            "action_name": "generate_user_intent",
            "action_params": {},
            "action_result_key": None,
            "is_system_action": True,
            "type": "start_action",
        },
        {
            "action_name": "generate_user_intent",
            "action_params": {},
            "action_result_key": None,
            "context_updates": None,
            "events": [{"intent": "express greeting", "type": "user_intent"}],
            "is_system_action": True,
            "return_value": None,
            "status": "success",
            "type": "action_finished",
        },
        {"intent": "express greeting", "type": "user_intent"},
        {
            "action_name": "fetch_profile",
            "action_params": {},
            "action_result_key": "account",
            "is_system_action": False,
            "type": "start_action",
        },
        {
            "action_name": "fetch_profile",
            "action_params": {},
            "action_result_key": "account",
            "context_updates": None,
            "events": [],
            "is_system_action": False,
            "return_value": {"name": "John"},
            "status": "success",
            "type": "action_finished",
        },
        {"data": {"account": {"name": "John"}}, "type": "context_update"},
        {"intent": "express greeting", "type": "bot_intent"},
        {
            "action_name": "generate_bot_message",
            "action_params": {},
            "action_result_key": None,
            "is_system_action": True,
            "type": "start_action",
        },
        {
            "action_name": "generate_bot_message",
            "action_params": {},
            "action_result_key": None,
            "context_updates": {},
            "events": [{"content": "Hello!", "type": "bot_said"}],
            "is_system_action": True,
            "return_value": None,
            "status": "success",
            "type": "action_finished",
        },
        {"content": "Hello!", "type": "bot_said"},
        {"type": "listen"},
    ]
