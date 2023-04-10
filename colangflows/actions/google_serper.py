import re

from langchain.utilities.google_serper import GoogleSerperAPIWrapper
from pydantic import validator

MAX_QUERY_LEN = 50


class GoogleSerper(GoogleSerperAPIWrapper):
    query: str

    @validator("query")
    def validate_query(cls, query: str):
        if not isinstance(query, str) or not query:
            raise ValueError("Query is not a valid string")
        if len(query) > MAX_QUERY_LEN:
            raise ValueError("Google Serper Query length exceeded limits")

        return query

    def validate_response(self, response: str) -> str:
        """Filter out IP addreess from the response."""

        ip_regex = re.compile(r"\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b")
        response = re.sub(ip_regex, "", response)
        return response

    def run(self) -> str:
        """Run query through Google Serper and parse result."""

        response = super().run(self.query)
        return self.validate_response(response)


# if __name__ == "__main__":
#     serp_obj = GoogleSerper(query="Who is the Joe Biden?")
#     output = serp_obj.run()
#     print(output)
