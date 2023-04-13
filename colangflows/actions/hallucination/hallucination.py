import logging
import random
import textwrap
from typing import Optional

from langchain import LLMChain, PromptTemplate
from langchain.llms import BaseLLM, OpenAI

from colangflows.actions.llm.generation import LLMGenerationActions
from colangflows.actions.llm.utils import get_first_nonempty_line

log = logging.getLogger(__name__)

HALLUCINATION_NUM_EXTRA_RESPONSES = 2


async def check_hallucination(
    context: Optional[dict] = None,
    llm: Optional[BaseLLM] = None,
    use_llm_checking: bool = True,
):
    """Checks if the last bot response is a hallucination."""

    bot_response = context.get("last_bot_message")
    last_bot_prompt = context.get("last_bot_prompt")

    if bot_response and last_bot_prompt:
        num_responses = HALLUCINATION_NUM_EXTRA_RESPONSES
        # Use beam search for the LLM call, to get several completions with only one call
        extra_llm = OpenAI(temperature=1, n=num_responses, best_of=num_responses)

        prompt = last_bot_prompt.pop("prompt")

        # Use the "generate" call from langchain to get all completions in the same response
        chain = LLMChain(prompt=prompt, llm=extra_llm)
        extra_llm_response = await chain.agenerate([last_bot_prompt])
        extra_llm_completions = []
        if len(extra_llm_response.generations) > 0:
            extra_llm_completions = extra_llm_response.generations[0]

        extra_responses = []
        i = 0
        while i < num_responses and i < len(extra_llm_completions):
            result = extra_llm_completions[i].text
            result = get_first_nonempty_line(result)
            # Strip the quotes, similar to the processing of responses in "generate_bot_message"
            if result and result[0] == '"':
                result = result[1:-1]
            extra_responses.append(result)
            i += 1

        if len(extra_responses) == 0:
            # Log message and return that no hallucination was found
            log.warning(
                f"No extra LLM responses were generated for '{bot_response}' hallucination check."
            )
            return False
        elif len(extra_responses) < num_responses:
            log.warning(
                f"Requested {num_responses} extra LLM responses for hallucination check, "
                f"received {len(extra_responses)}."
            )

        if use_llm_checking:
            # Only support LLM-based agreement check in current version
            hallucination_check_template = textwrap.dedent(
                """
            You are given a task to identify if the hypothesis is in agreement with the context below.
            You will only use the contents of the context and not rely on external knowledge.
            Answer with yes/no. "context": {paragraph} "hypothesis": {statement} "agreement":
            """
            )

            prompt = PromptTemplate(
                template=hallucination_check_template,
                input_variables=["statement", "paragraph"],
            )

            hallucination_check_chain = LLMChain(prompt=prompt, llm=llm, verbose=True)
            agreement = await hallucination_check_chain.apredict(
                statement=bot_response, paragraph=". ".join(extra_responses)
            )

            agreement = agreement.lower().strip()
            log.info(f"Agreement result for looking for hallucination is {agreement}.")

            # Return True if the hallucination check fails
            return "no" in agreement
        else:
            # TODO Implement BERT-Score based consistency method proposed by SelfCheckGPT paper
            # See details: https://arxiv.org/abs/2303.08896
            return False

    return False
