from typing import Optional

import pytest

from colangflows import RailsConfig
from colangflows.flows.runtime import Runtime
from tests.utils import FakeLLM


@pytest.mark.asyncio
async def test_1():
    config = RailsConfig.parse_obj(
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

    runtime = Runtime(config=config, llm=llm)
    runtime.register_action("compute", compute)

    events = [{"type": "user_said", "content": "Hello!"}]

    new_events = await runtime.generate_events(events)

    assert new_events == [
        {"action_name": "generate_user_intent", "system": True, "type": "start_action"},
        {
            "action_name": "generate_user_intent",
            "events": [{"intent": "express greeting", "type": "user_intent"}],
            "return_value": None,
            "status": "success",
            "system": True,
            "type": "action_finished",
        },
        {"intent": "express greeting", "type": "user_intent"},
        {"intent": "express greeting", "type": "bot_intent"},
        {"action_name": "generate_bot_message", "system": True, "type": "start_action"},
        {
            "action_name": "generate_bot_message",
            "events": [{"content": "Hello! How are you?", "type": "bot_said"}],
            "return_value": None,
            "status": "success",
            "system": True,
            "type": "action_finished",
        },
        {"content": "Hello! How are you?", "type": "bot_said"},
        {"action_name": "generate_next_step", "system": True, "type": "start_action"},
        {
            "action_name": "generate_next_step",
            "events": None,
            "return_value": None,
            "status": "success",
            "system": True,
            "type": "action_finished",
        },
        {"type": "listen"},
    ]

    events.extend(new_events)
    events.append({"type": "user_said", "content": "2 + 3"})

    new_events = await runtime.generate_events(events)

    assert new_events == [
        {"action_name": "generate_user_intent", "system": True, "type": "start_action"},
        {
            "action_name": "generate_user_intent",
            "events": [{"intent": "ask math question", "type": "user_intent"}],
            "return_value": None,
            "status": "success",
            "system": True,
            "type": "action_finished",
        },
        {"intent": "ask math question", "type": "user_intent"},
        {"action_name": "compute", "system": False, "type": "start_action"},
        {
            "action_name": "compute",
            "events": [],
            "return_value": 5,
            "status": "success",
            "type": "action_finished",
        },
        {"intent": "provide math response", "type": "bot_intent"},
        {"action_name": "generate_bot_message", "system": True, "type": "start_action"},
        {
            "action_name": "generate_bot_message",
            "events": [{"content": "The answer is 5", "type": "bot_said"}],
            "return_value": None,
            "status": "success",
            "system": True,
            "type": "action_finished",
        },
        {"content": "The answer is 5", "type": "bot_said"},
        {"intent": "ask if user happy", "type": "bot_intent"},
        {"action_name": "generate_bot_message", "system": True, "type": "start_action"},
        {
            "action_name": "generate_bot_message",
            "events": [
                {"content": "Are you happy with the result?", "type": "bot_said"}
            ],
            "return_value": None,
            "status": "success",
            "system": True,
            "type": "action_finished",
        },
        {"content": "Are you happy with the result?", "type": "bot_said"},
        {"type": "listen"},
    ]
