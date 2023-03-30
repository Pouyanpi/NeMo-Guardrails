import logging
import os
from typing import Optional
from urllib import parse

import aiohttp

log = logging.getLogger(__name__)

APP_ID = os.environ.get("WOLFRAM_ALPHA_APP_ID")
API_URL_BASE = f"https://api.wolframalpha.com/v2/result?appid={APP_ID}"


async def wolfram_alpha_request(
    query: Optional[str] = None, context: Optional[dict] = None
):
    """Makes a request to the Wolfram Alpha API

    :param context: The context for the execution of the action.
    :param query: The query for Wolfram.
    """
    # If we don't have an explicit query, we take the last user message
    if query is None and context is not None:
        query = context.get("last_user_message") or "2+3"

    if query is None:
        raise Exception("No query was provided to Wolfram Alpha.")

    url = API_URL_BASE + "&" + parse.urlencode({"i": query})

    log.info(f"Wolfram Alpha: executing request for: {query}")

    async with aiohttp.ClientSession() as session:
        async with session.get(url) as resp:
            if resp.status != 200:
                raise Exception(
                    f"Got status code {resp.status} to WolframAlpha engine request: {await resp.text()}"
                )

            result = await resp.text()

            log.info(f"Wolfram Alpha: the result was {result}.")
            return result
