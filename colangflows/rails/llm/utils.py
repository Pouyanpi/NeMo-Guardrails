from typing import List


def get_history_cache_key(messages: List[dict], include_last: bool) -> str:
    """Computes the cache key for a sequence of messages and a config id."""
    user_messages = [msg["content"] for msg in messages[0:-1] if msg["role"] == "user"]
    if include_last:
        user_messages.append(messages[-1]["content"])

    history_cache_key = ":".join(user_messages)

    return history_cache_key
