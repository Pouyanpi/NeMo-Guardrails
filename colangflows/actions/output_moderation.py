import logging
import random
from typing import Optional

from langchain import LLMChain, PromptTemplate
from langchain.llms import BaseLLM
log = logging.getLogger(__name__)

async def output_moderation(
    context: Optional[dict] = None,
    llm: Optional[BaseLLM] = None,
):
    """Checks if the bot response is appropriate and passes moderation."""

    bot_response = context.get("last_bot_message")
    if bot_response:
        output_moderation_template = "model_output: {bot_response} \n\n Is this output legal, ethical and not harmful to any person? Answer with yes/no."

        prompt = PromptTemplate(
            template=output_moderation_template, input_variables=["bot_response"]
        )

        output_moderation_chain = LLMChain(prompt=prompt, llm=llm)
        check = await output_moderation_chain.apredict(bot_response=bot_response)

        check = check.lower().strip()
        log.info(f"Output moderation check result is {check}.")

        if "no" in check:
            return False
    return True
