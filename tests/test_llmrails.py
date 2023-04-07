from typing import Optional

import pytest

from colangflows.rails import LLMRails, RailsConfig
from tests.utils import FakeLLM


@pytest.fixture
def rails_config():
    return RailsConfig.parse_object(
        {
            "models": [
                {
                    "type": "main",
                    "engine": "fake",
                    "model": "fake",
                }
            ],
            "user_messages": {
                "express greeting": ["Hello!"],
                "ask math question": ["What is 2 + 2?", "5 + 9"],
            },
            "flows": [
                {
                    "elements": [
                        {"user": "express greeting"},
                        {"bot": "express greeting"},
                    ]
                },
                {
                    "elements": [
                        {"user": "ask math question"},
                        {"execute": "compute"},
                        {"bot": "provide math response"},
                        {"bot": "ask if user happy"},
                    ]
                },
            ],
            "bot_messages": {
                "express greeting": ["Hello! How are you?"],
                "provide response": ["The answer is 234", "The answer is 1412"],
            },
        }
    )


@pytest.mark.asyncio
async def test_1(rails_config):
    llm = FakeLLM(
        responses=[
            "  express greeting",
            "  ask math question",
            '  "The answer is 5"',
            '  "Are you happy with the result?"',
        ]
    )

    async def compute(context: dict, what: Optional[str] = "2 + 3"):
        return eval(what)

    llm_rails = LLMRails(config=rails_config, llm=llm)
    llm_rails.runtime.register_action(compute)

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
            "events": [{"intent": "express greeting", "type": "user_intent"}],
            "is_system_action": True,
            "return_value": None,
            "status": "success",
            "type": "action_finished",
        },
        {"intent": "express greeting", "type": "user_intent"},
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
            "events": [{"content": "Hello! How are you?", "type": "bot_said"}],
            "is_system_action": True,
            "return_value": None,
            "status": "success",
            "type": "action_finished",
        },
        {"content": "Hello! How are you?", "type": "bot_said"},
        {"type": "listen"},
    ]

    events.extend(new_events)
    events.append({"type": "user_said", "content": "2 + 3"})

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
            "events": [{"intent": "ask math question", "type": "user_intent"}],
            "is_system_action": True,
            "return_value": None,
            "status": "success",
            "type": "action_finished",
        },
        {"intent": "ask math question", "type": "user_intent"},
        {
            "action_name": "compute",
            "action_params": {},
            "action_result_key": None,
            "is_system_action": False,
            "type": "start_action",
        },
        {
            "action_name": "compute",
            "action_params": {},
            "action_result_key": None,
            "events": [],
            "is_system_action": False,
            "return_value": 5,
            "status": "success",
            "type": "action_finished",
        },
        {"intent": "provide math response", "type": "bot_intent"},
        {
            "action_name": "generate_bot_message",
            "action_params": {},
            "action_result_key": None,
            "is_system_action": True,
            "type": "start_action",
        },
        {"data": {"relevant_chunks": ""}, "type": "context_update"},
        {
            "action_name": "generate_bot_message",
            "action_params": {},
            "action_result_key": None,
            "events": [{"content": "The answer is 5", "type": "bot_said"}],
            "is_system_action": True,
            "return_value": None,
            "status": "success",
            "type": "action_finished",
        },
        {"content": "The answer is 5", "type": "bot_said"},
        {"intent": "ask if user happy", "type": "bot_intent"},
        {
            "action_name": "generate_bot_message",
            "action_params": {},
            "action_result_key": None,
            "is_system_action": True,
            "type": "start_action",
        },
        {"data": {"relevant_chunks": ""}, "type": "context_update"},
        {
            "action_name": "generate_bot_message",
            "action_params": {},
            "action_result_key": None,
            "events": [
                {"content": "Are you happy with the result?", "type": "bot_said"}
            ],
            "is_system_action": True,
            "return_value": None,
            "status": "success",
            "type": "action_finished",
        },
        {"content": "Are you happy with the result?", "type": "bot_said"},
        {"type": "listen"},
    ]


@pytest.mark.asyncio
async def test_2(rails_config):
    llm = FakeLLM(
        responses=[
            "  express greeting",
            "  ask math question",
            '  "The answer is 5"',
            '  "Are you happy with the result?"',
        ]
    )

    async def compute(what: Optional[str] = "2 + 3"):
        return eval(what)

    llm_rails = LLMRails(config=rails_config, llm=llm)
    llm_rails.runtime.register_action(compute)

    messages = [{"role": "user", "content": "Hello!"}]
    bot_message = await llm_rails.generate_async(messages=messages)

    assert bot_message == {"role": "assistant", "content": "Hello! How are you?"}
    messages.append(bot_message)

    messages.append({"role": "user", "content": "2 + 3"})
    bot_message = await llm_rails.generate_async(messages=messages)
    assert bot_message == {
        "role": "assistant",
        "content": "The answer is 5\nAre you happy with the result?",
    }
