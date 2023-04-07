from colangflows.rails import RailsConfig
from tests.utils import TestChat


def test_1():
    """Test that setting variables in context works correctly."""
    config = RailsConfig.from_content(
        """
        define user express greeting
            "hello"

        define flow
            user express greeting

            $name = "John"
            if $name == "John"
              bot greet back John
        """
    )
    chat = TestChat(
        config,
        llm_completions=[
            "  express greeting",
            '  "Hello John!"',
        ],
    )

    chat >> "hello there!"
    chat << "Hello John!"
