from typing import List


def get_colang_history(events: List[dict], include_texts: bool = True):
    """Creates a history of user messages and bot responses in colang format.
    user "Hi, how are you today?"
      express greeting
    bot express greeting
      "Greetings! I am the official NVIDIA Benefits Ambassador AI bot and I'm here to assist you."
    user "What can you help me with?"
      ask capabilities
    bot inform capabilities
      "As an AI, I can provide you with a wide range of services, such as ..."

    """

    history = ""
    for event in events:
        if event["type"] == "user_said" and include_texts:
            history += f'user "{event["content"]}"\n'
        elif event["type"] == "user_intent":
            if include_texts:
                history += f'  {event["intent"]}\n'
            else:
                history += f'user {event["intent"]}\n'
        elif event["type"] == "bot_intent":
            history += f'bot {event["intent"]}\n'
        elif event["type"] == "bot_said" and include_texts:
            history += f'  "{event["content"]}"\n'
        # We skip system actions from this log
        elif event["type"] == "start_action" and not event.get("system"):
            history += f'execute {event["action_name"]}\n'
        elif event["type"] == "action_finished" and not event.get("system"):
            history += f'# The result was {event["return_value"]}\n'

    return history


def flow_to_colang(flow: dict):
    """Converts a flow to colang format.

    Example flow:
    ```
      - user: ask capabilities
      - bot: inform capabilities
    ```

    to colang:

    ```
    user ask capabilities
    bot inform capabilities
    ```

    """

    colang_flow = ""
    for step in flow["elements"]:
        if "user" in step:
            colang_flow += f'user {step["user"]}\n'
        elif "bot" in step:
            colang_flow += f'bot {step["bot"]}\n'

    return colang_flow
