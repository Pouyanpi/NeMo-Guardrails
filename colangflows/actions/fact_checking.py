import logging
from typing import Optional

from langchain import LLMChain, PromptTemplate
from langchain.llms import BaseLLM

log = logging.getLogger(__name__)


async def check_facts(
    context: Optional[dict] = None,
    llm: Optional[BaseLLM] = None,
):
    """Checks the facts for the bot response."""

    evidence = context.get("relevant_chunks", [])
    bot_response = context.get("last_bot_message")

    if evidence:
        fact_check_template = """
            You are given a task to identify if the hypothesis is grounded and entailed to the evidence.
            You will only use the contents of the evidence and not rely on external knowledge.
            Answer with yes/no. "evidence": {evidence} "hypothesis": {response} "entails":"""

        prompt = PromptTemplate(
            template=fact_check_template, input_variables=["evidence", "response"]
        )

        fact_check_chain = LLMChain(prompt=prompt, llm=llm)
        entails = fact_check_chain.predict(evidence=evidence, response=bot_response)

        entails = entails.lower().strip()
        log.info(f"Entailment result is {entails}.")

        return "yes" in entails

    # If there was no evidence, we always return true
    return True
