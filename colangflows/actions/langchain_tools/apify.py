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

    def run(
        self,
        run_input: Dict,
        dataset_mapping_function: Callable[[Dict], Document],
        *,
        build: Optional[str] = None,
        memory_mbytes: Optional[int] = None,
        timeout_secs: Optional[int] = None,
    ):
        return self.call_actor(
            actor_id=self.actor_id,
            run_input=run_input,
            dataset_mapping_function=dataset_mapping_function,
            build=build,
            memory_mbytes=memory_mbytes,
            timeout_secs=timeout_secs,
        )

    async def arun(
        self,
        run_input: Dict,
        dataset_mapping_function: Callable[[Dict], Document],
        *,
        build: Optional[str] = None,
        memory_mbytes: Optional[int] = None,
        timeout_secs: Optional[int] = None,
    ):
        response = await self.acall_actor(
            actor_id=self.actor_id,
            run_input=run_input,
            dataset_mapping_function=dataset_mapping_function,
            build=build,
            memory_mbytes=memory_mbytes,
            timeout_secs=timeout_secs,
        )

        return response
