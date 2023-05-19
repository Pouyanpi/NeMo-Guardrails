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

from abc import ABC, abstractmethod
from typing import Dict, List


class DocumentParser(ABC):
    @abstractmethod
    def split_document_in_topic_chunks(
        self, content: str, max_chunk_size: int = 400
    ) -> List[Dict[str, str]]:
        """Abstract method to split a document into chunks.

        :param content: The markdown content to be split.
        :param max_chunk_size: The maximum size of a chunk.
        """
        raise NotImplementedError
