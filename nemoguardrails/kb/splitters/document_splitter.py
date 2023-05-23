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

"""Abstract class for document splitters."""

from abc import ABC, abstractmethod
from typing import Dict, List


class DocumentParser(ABC):
    @abstractmethod
    def split(
        self, content: str, max_chunk_size: int = 400
    ) -> List[Dict[str, str]]:
        """Abstract method to split a document into chunks.

        :param content: The markdown content to be split.
        :param max_chunk_size: The maximum size of a chunk.
        """
        raise NotImplementedError



class DocumentSplitter(ABC):
    """Abstract class for document splitters."""

    def __init__(self, splitter_name: str, **kwargs):
        """
        Initialize a document splitter.

        :param splitter_name: The name of the splitter.
        :type splitter_name: str
        """
        self._splitter_name = splitter_name

    @abstractmethod
    def to_topic(self, splits: list[str]) -> str:
        """
        Convert a list of splits to a topic.

        :param splits: The splits to convert.
        :type splits: list[str]
        :return: The topic.
        :rtype: str
        """
        raise NotImplementedError
    
    @abstractmethod
    def split(self, text: str) -> list[str]:
        """
        Split a document into chunks.

        :param text: The text to split.
        :type text: str
        :return: The list of chunks.
        :rtype: list[str]
        """
        raise NotImplementedError