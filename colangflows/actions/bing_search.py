import re

from langchain.utilities.bing_search import BingSearchAPIWrapper
from pydantic import validator

MAX_QUERY_LEN = 50


class BingSearch(BingSearchAPIWrapper):
    query: str

    @validator("query")
    def validate_query(cls, query: str):
        if not isinstance(query, str) or not query:
            raise ValueError("Query is not a valid string")
        if len(query) > MAX_QUERY_LEN:
            raise ValueError("Bing Search Query length exceeded limits")

        return query

    def validate_response(self, response: str) -> str:
        """Filter out IP addreess from the response."""

        ip_regex = re.compile(r"\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b")
        response = re.sub(ip_regex, "", response)
        return response

    def run(self) -> str:
        """Run query through Bing Search and parse result."""

        response = super().run(self.query)
        return self.validate_response(response)


# if __name__ == "__main__":
#     search_obj = BingSearch(query="Who is the Joe Biden?")
#     output = search_obj.run()
#     print(output)
