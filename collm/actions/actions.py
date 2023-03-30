from dataclasses import dataclass
from typing import Any, List, Optional


@dataclass
class ActionResult:
    # The value returned by the action
    return_value: Optional[Any] = None

    # The events that should be added to the stream
    events: Optional[List[dict]] = None
