from dataclasses import dataclass, field
from typing import Any, List, Optional


# A decorator that sets a property on the function to indicate if it's a system action or not.
def action(is_system_action: bool = False, name: Optional[str] = None):
    def decorator(fn_or_cls):
        fn_or_cls.action_meta = {
            "name": name or fn_or_cls.__name__,
            "is_system_action": is_system_action,
        }
        return fn_or_cls

    return decorator


@dataclass
class ActionResult:
    # The value returned by the action
    return_value: Optional[Any] = None

    # The events that should be added to the stream
    events: Optional[List[dict]] = None

    # The updates made to the context by this action
    context_updates: Optional[dict] = field(default_factory=dict)
