from colangflows.rails import RailsConfig
from tests.utils import TestChat

config = RailsConfig.from_content(
    """
    define user express greeting
        "hello"

    define flow
        user express greeting
        bot express greeting
        bot ask wellfare

        when user express positive emotion
            bot express positive emotion

        else when user express negative emotion
            bot express empathy

    """
)


def test_1():
    """Test that branching with `when` works correctly."""
    chat = TestChat(
        config,
        llm_completions=[
            "  express greeting",
            '  "Hello there!"',
            '  "How are you feeling?"',
            "  express negative emotion",
            '  "I\'m sorry to hear that."',
        ],
    )

    chat >> "Hello!"
    chat << "Hello there!\nHow are you feeling?"
    chat >> "kind of bad"
    chat << "I'm sorry to hear that."


def test_2():
    """Test that branching with `when` works correctly."""
    chat = TestChat(
        config,
        llm_completions=[
            "  express greeting",
            '  "Hello there!"',
            '  "How are you feeling?"',
            "  express positive emotion",
            '  "Awesome!"',
        ],
    )

    chat >> "Hello!"
    chat << "Hello there!\nHow are you feeling?"
    chat >> "having a good day"
    chat << "Awesome!"
