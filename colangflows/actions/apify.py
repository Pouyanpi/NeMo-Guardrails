from typing import Callable, Dict, Optional

from langchain.document_loaders.base import Document
from langchain.utilities.apify import ApifyWrapper
from pydantic import validator

MAX_QUERY_LEN = 50


class Apify(ApifyWrapper):
    actor_id: str

    @validator("actor_id")
    def validate_query(cls, query: str):
        if not isinstance(query, str) or not query:
            raise ValueError("Actor ID is not a valid string")
        if len(query) > MAX_QUERY_LEN:
            raise ValueError("Apify Actor ID length exceeded limits")

        return query

    def call_actor(
        self,
        run_input: Dict,
        dataset_mapping_function: Callable[[Dict], Document],
        *,
        build: Optional[str] = None,
        memory_mbytes: Optional[int] = None,
        timeout_secs: Optional[int] = None,
    ):
        return super().call_actor(
            actor_id=self.actor_id,
            run_input=run_input,
            dataset_mapping_function=dataset_mapping_function,
            build=build,
            memory_mbytes=memory_mbytes,
            timeout_secs=timeout_secs,
        )

    async def acall_actor(
        self,
        run_input: Dict,
        dataset_mapping_function: Callable[[Dict], Document],
        *,
        build: Optional[str] = None,
        memory_mbytes: Optional[int] = None,
        timeout_secs: Optional[int] = None,
    ):
        response = await super().acall_actor(
            actor_id=self.actor_id,
            run_input=run_input,
            dataset_mapping_function=dataset_mapping_function,
            build=build,
            memory_mbytes=memory_mbytes,
            timeout_secs=timeout_secs,
        )

        return response


# if __name__ == "__main__":
#     search_obj = BingSearch(query="Who is the Joe Biden?")
#     output = search_obj.run()
#     print(output)
