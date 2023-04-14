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

from langchain.utilities.wikipedia import WikipediaAPIWrapper
from pydantic import validator

from colangflows.actions.actions import action

MAX_QUERY_LEN = 50


@action()
class Wikipedia(WikipediaAPIWrapper):
    query: str

    @validator("query")
    def validate_query(cls, query: str):
        if not query:
            raise ValueError("Query cannot be empty")
        if len(query) > MAX_QUERY_LEN:
            raise ValueError("Wikipedia Query length exceeded limits")

        return query

    def validate_response(self, response: str) -> str:
        """Filter out IP addreess from the response."""

        ip_regex = re.compile(r"\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b")
        response = re.sub(ip_regex, "", response)
        return response

    def run(self) -> str:
        """Run query through Wikipedia and parse result."""

        response = super().run(self.query)
        return self.validate_response(response)
