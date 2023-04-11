import re
from typing import Dict, Optional
from urllib.parse import quote

from langchain.utilities.zapier import ZapierNLAWrapper
from pydantic import validator

MAX_QUERY_LEN = 500


class Zapier(ZapierNLAWrapper):
    instructions: str
    action_id: str

    @validator("instructions")
    def validate_instruction(cls, instructions):
        if not instructions:
            raise ValueError("Zapier Instruction is not a valid string")
        if len(instructions) > MAX_QUERY_LEN:
            raise ValueError("Zapier Instruction length exceeded limits")

        return instructions

    @validator("action_id")
    def validate_action_id(cls, action_id):
        if not isinstance(action_id, str) or not action_id:
            raise ValueError("Query is not a valid string")

        return quote(action_id, safe="")

    def validate_response(self, response: str) -> str:
        """Filter out IP addreess from the response."""

        ip_regex = re.compile(r"\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b")
        response = re.sub(ip_regex, "", response)
        return response

    def run(self, params: Optional[Dict] = None) -> str:
        """Run query through Zapier and parse result."""

        response = super().run(self.action_id, self.instructions, params)
        return self.validate_response(response.get("description", ""))

    def preview(self, params: Optional[Dict] = None) -> str:
        """Calls the review method of Zapier to get a preview of the params
        that have been guessed by the AI instead of executing the action."""

        response = super().preview(self.action_id, self.instructions, params)
        return self.validate_response(response.get("Message_Text", ""))
