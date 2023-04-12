"""Demo script."""
import logging

from colangflows.rails import LLMRails, RailsConfig

logging.basicConfig(level=logging.INFO)

COLANG_CONFIG = """
define user ask service status
  "what is the status of my service"
  "is the service up?"
  "is the service down?"

define flow
  user ask service status
  $status = execute check_service_status
  bot inform service status
"""

YAML_CONFIG = """
models:
  - type: main
    engine: openai
    model: text-davinci-003
"""


async def check_service_status():
    return "online"


def demo():
    """Quick demo using LLMRails with config from dict."""
    config = RailsConfig.from_content(COLANG_CONFIG, YAML_CONFIG)

    app = LLMRails(config)
    app.register_action(check_service_status)

    history = [{"role": "user", "content": "Tell me if the service is up"}]
    result = app.generate(messages=history)
    print(result)


if __name__ == "__main__":
    demo()
