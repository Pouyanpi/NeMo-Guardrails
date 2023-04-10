import re

from langchain.tools.human.tool import HumanInputRun
from pydantic import validator

MAX_QUERY_LEN = 50


class Human(HumanInputRun):
    query: str

    @validator("query")
    def validate_query(cls, query: str):
        if not isinstance(query, str) or not query:
            raise ValueError("Query is not a valid string")
        if len(query) > MAX_QUERY_LEN:
            raise ValueError("Human Action Query length exceeded limits")

        return query

    def validate_response(self, response: str) -> str:
        """Filter out IP addreess from the response."""

        ip_regex = re.compile(r"\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b")
        response = re.sub(ip_regex, "", response)
        return response

    def run(self) -> str:
        response = self._run(self.query)
        return self.validate_response(response)


# if __name__ == "__main__":
#     serp_obj = Human(query="Who is the Joe Biden?")
#     output = serp_obj.run()
#     print(output)
