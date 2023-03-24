from typing import Optional

import pytest

from collm import RailsConfig
from collm.runtime.runtime import Runtime
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
        {"type": "user_intent", "intent": "express greeting"},
        {"type": "bot_intent", "intent": "express greeting"},
        {"type": "bot_said", "content": "Hello! How are you?"},
        {"type": "listen"},
    ]

    events.extend(new_events)
    events.append({"type": "user_said", "content": "2 + 3"})

    new_events = await runtime.generate_events(events)

    assert new_events == [
        {"type": "user_intent", "intent": "ask math question"},
        {"type": "start_action", "action_name": "compute"},
        {
            "type": "action_finished",
            "action_name": "compute",
            "status": "success",
            "return_value": 5,
        },
        {"type": "bot_intent", "intent": "provide math response"},
        {"type": "bot_said", "content": "The answer is 5"},
        {"type": "bot_intent", "intent": "ask if user happy"},
        {"type": "bot_said", "content": "Are you happy with the result?"},
        {"type": "listen"},
    ]
