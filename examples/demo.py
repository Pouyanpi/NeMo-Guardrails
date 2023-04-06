"""Demo script."""
import logging

from colangflows.rails import LLMRails, RailsConfig

logging.basicConfig(level=logging.INFO)


def demo():
    """Quick demo using LLMRails with config from dict."""
    config = RailsConfig.parse_object(
        {
            "models": [
                {"type": "main", "engine": "openai", "model": "text-davinci-003"}
            ],
            "instructions": [
                {
                    "type": "general",
                    "content": "Use a maximum of five words when answering any request.",
                }
            ],
        }
    )

    app = LLMRails(config)

    # Brainstorming for registering additional handlers
    # app.register_handler("before_action", {"action_name": "inform_get"}, handler)
    # app.register_handler("after_action", {"action_name": "inform_get"}, handler)
    # app.register_handler("before_bot_said", fact_checking)

    history = [{"role": "user", "content": "Hello! How are you?"}]
    result = app.generate(messages=history)
    print(result)


if __name__ == "__main__":
    demo()
