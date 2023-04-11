import re
from typing import Any, List, Optional

from langchain.utilities.searx_search import SearxSearchWrapper
from pydantic import validator

MAX_QUERY_LEN = 5


class SearxSearch(SearxSearchWrapper):
    query: str
    engines: Optional[List[str]] = []
    categories: Optional[List[str]] = []
    query_suffix: Optional[str] = ""

    @validator("query")
    def validate_query(cls, query: str):
        if not query:
            raise ValueError("Query is not a valid string")
        if len(query) > MAX_QUERY_LEN:
            raise ValueError("Searx Search Query length exceeded limits")

        return query

    def validate_response(self, response: str) -> str:
        """Filter out IP addreess from the response."""

        ip_regex = re.compile(r"\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b")
        response = re.sub(ip_regex, "", response)
        return response

    def run(self, **kwargs: Any) -> str:
        """Run query through Searx Search and parse result."""

        response = super().run(
            self.query, self.engines, self.categories, self.query_suffix, **kwargs
        )
        return self.validate_response(response)

    async def arun(self, **kwargs: Any) -> str:
        """Call async run method of Searx Search langchain tool."""

        response = await super().arun(
            self.query, self.engines, self.query_suffix, **kwargs
        )
        return self.validate_response(response)
