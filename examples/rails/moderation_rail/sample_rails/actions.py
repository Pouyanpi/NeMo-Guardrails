from colangflows.actions import action
from typing import Any, List, Optional
import os

@action()
async def block_list(
    file_name: Optional[str] = None,
    context: Optional[dict] = None
):
    lines = None
    bot_response = context.get("last_bot_message")
    
    with open(file_name) as f:
        lines = [line.rstrip() for line in f]

    for line in lines:
        if line in bot_response:
            return True
    return False
