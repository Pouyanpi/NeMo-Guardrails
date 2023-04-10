import re
from typing import Any, Dict

from langchain.utilities.wikipedia import WikipediaAPIWrapper
from langchain.utils import get_from_dict_or_env
from pydantic import BaseModel, root_validator

MAX_QUERY_LEN = 50


class Wikipedia(WikipediaAPIWrapper):
    query: str

    @root_validator()
    def validate_query(cls, values: Dict):
        query = get_from_dict_or_env(values, "query", "")
        if not isinstance(query, str) or not query:
            raise ValueError("Query is not a valid string")
        if len(query) > MAX_QUERY_LEN:
            raise ValueError("Wikipedia Query length exceeded limits")

        return values

    def validate_response(self, response: str) -> str:
        """Filter out IP addreess from the response."""

        ip_regex = re.compile(r"\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b")
        response = re.sub(ip_regex, "", response)
        return response

    def run(self) -> str:
        """Run query through Wikipedia and parse result."""

        response = super().run(self.query)
        return self.validate_response(response)
