import re

from langchain.utilities.openweathermap import OpenWeatherMapAPIWrapper
from pydantic import validator

MAX_LOCATION_LEN = 50


class OpenWeatherMap(OpenWeatherMapAPIWrapper):
    location: str

    @validator("location")
    def validate_location(cls, location: str):
        if not isinstance(location, str) or not location:
            raise ValueError("Location is not a valid string")
        if len(location) > MAX_LOCATION_LEN:
            raise ValueError("OpenWeatherMap location length exceeded limits")

        return location

    def validate_response(self, response: str) -> str:
        """Filter out IP addreess from the response."""

        ip_regex = re.compile(r"\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b")
        response = re.sub(ip_regex, "", response)
        return response

    def run(self) -> str:
        """Run query through OpenWeatherMap and parse result."""

        response = super().run(self.location)
        return self.validate_response(response)


# if __name__ == "__main__":
#     owm_obj = OpenWeatherMap(location="santa clara")
#     output = owm_obj.run()
#     print(output)
