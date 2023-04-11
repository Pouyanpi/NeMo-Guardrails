import logging
import random
import textwrap
from typing import Optional

from langchain import LLMChain, PromptTemplate
from langchain.llms import BaseLLM, OpenAI

from colangflows.actions.llm.generation import LLMGenerationActions
from colangflows.actions.llm.utils import get_first_nonempty_line

log = logging.getLogger(__name__)


async def check_hallucination(
    context: Optional[dict] = None,
    llm: Optional[BaseLLM] = None,
    use_llm_checking: bool = True,
):
    """Checks if the last bot response is a hallucination."""

    bot_response = context.get("last_bot_message")

    if bot_response:
        num_responses = 2
        # TODO use beam search, with several results in the same response
        # extra_llm = OpenAI(temperature=1, n=num_responses, best_of=4)
        extra_llm = OpenAI(temperature=1)

        prompt = LLMGenerationActions.last_bot_prompt["prompt"]

        chain = LLMChain(prompt=prompt, llm=extra_llm)
        results = []
        for _ in range(num_responses):
            result = await chain.apredict(
                history=LLMGenerationActions.last_bot_prompt["history"],
                examples=LLMGenerationActions.last_bot_prompt["examples"],
                relevant_chunks=LLMGenerationActions.last_bot_prompt["relevant_chunks"],
                sample_conversation=LLMGenerationActions.last_bot_prompt[
                    "sample_conversation"
                ],
                general_instruction=LLMGenerationActions.last_bot_prompt[
                    "general_instruction"
                ],
                sample_conversation_two_turns=LLMGenerationActions.last_bot_prompt[
                    "sample_conversation_two_turns"
                ],
            )

            result = get_first_nonempty_line(result)
            # Strip the quotes
            if result and result[0] == '"':
                result = result[1:-1]
            results.append(result)

        if use_llm_checking:
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
                statement=bot_response, paragraph=". ".join(results)
            )

            agreement = agreement.lower().strip()
            log.info(f"Agreement result for looking for hallucination is {agreement}.")

            # Return True if the hallucination check fails
            return "no" in agreement

        bot_utterance = result

        return True
    return False
