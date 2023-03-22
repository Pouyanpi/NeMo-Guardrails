"""Demo script."""
import logging

from collm.config import RailsConfig
from collm.llmrails import LLMRails

logging.basicConfig(level=logging.INFO)


def demo():
    """Quick demo using LLMRails with config from dict."""
    config = RailsConfig.parse_obj(
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

    history = [{"role": "user", "content": "Hello! How are you?"}]
    result = app.generate(messages=history)
    print(result)


if __name__ == "__main__":
    demo()
