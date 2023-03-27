import logging
import random
from typing import Optional

log = logging.getLogger(__name__)


async def check_facts(
    query: Optional[str] = None,
    context: Optional[dict] = None,
    runtime: Optional["Runtime"] = None,
):
    """Checks the facts for the bot response."""

    llm = runtime.llm

    # TODO: fetch the relevant chunks
    #  they should be in context["relevant_chunks"]
    relevant_chunks = context.get("relevant_chunks", [])
    last_bot_message = context.get("last_bot_message")

    # TODO: use the LLM instance to check the facts.

    # Provide a random response of whether the answer is correct or not
    return random.choice(["The response is correct.", "The answer is not correct."])
