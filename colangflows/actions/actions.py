from dataclasses import dataclass, field
from typing import Any, List, Optional


# A decorator that sets a property on the function to indicate if it's a system action or not.
def action(is_system_action: bool, name: Optional[str] = None):
    def decorator(func):
        func.action_meta = {
            "name": name or func.__name__,
            "is_system_action": is_system_action,
        }
        return func

    return decorator


@dataclass
class ActionResult:
    # The value returned by the action
    return_value: Optional[Any] = None

    # The events that should be added to the stream
    events: Optional[List[dict]] = None

    # The updates made to the context by this action
    context_updates: Optional[dict] = field(default_factory=dict)


# A decorator that sets a property on the class to indicate if it's a action or not.
def base_action(cls):
    cls.is_action = True
    return cls
