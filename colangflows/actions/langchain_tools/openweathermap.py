# SPDX-FileCopyrightText: Copyright (c) 2023 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: Apache-2.0
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import re

from langchain.utilities.openweathermap import OpenWeatherMapAPIWrapper
from pydantic import validator

MAX_LOCATION_LEN = 50


class OpenWeatherMap(OpenWeatherMapAPIWrapper):
    location: str

    @validator("location")
    def validate_location(cls, location: str):
        if not location:
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
