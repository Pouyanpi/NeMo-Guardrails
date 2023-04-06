import pytest

from colangflows.actions.actions import ActionResult
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
            },
            "flows": [
                {
                    "elements": [
                        {"user": "express greeting"},
                        {"execute": "increase_counter"},
                        {"bot": "express greeting"},
                    ]
                }
            ],
            "bot_messages": {
                "express greeting": ["Hello! How are you?"],
            },
        }
    )


@pytest.mark.asyncio
async def test_simple_context_update_from_action(rails_config):
    llm = FakeLLM(
        responses=[
            "  express greeting",
            "  express greeting",
        ]
    )

    async def increase_counter(context: dict):
        counter = context.get("counter", 0) + 1
        return ActionResult(context_updates={"counter": counter})

    llm_rails = LLMRails(config=rails_config, llm=llm)
    llm_rails.runtime.register_action(increase_counter)

    events = [{"type": "user_said", "content": "Hello!"}]

    new_events = await llm_rails.runtime.generate_events(events)

    events.extend(new_events)
    events.append({"type": "user_said", "content": "Hello!"})

    new_events = await llm_rails.runtime.generate_events(events)

    # The last event before listen should be a context update for the counter to "2"
    assert {"type": "context_update", "data": {"counter": 2}} in new_events
    assert new_events[-1] == {"type": "listen"}
