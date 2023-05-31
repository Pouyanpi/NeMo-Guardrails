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
from typing import Any, ClassVar, Dict, List, Type

from pydantic import BaseModel

from .registered import RegisteredSplitter, SplitterRegistry

# from . import SPLITTERS


class Topic(BaseModel):
    title: str
    body: str
    metadata: Dict[str, Any] = {}


class BaseSplitter(RegisteredSplitter, ABC):
    """Base class for all splitters."""

    name: ClassVar = None

    @abstractmethod
    def split_text(self, text: str) -> list[str]:
        """
        Split a text into chunks.

        :param text: The text to split.
        :type text: str
        :return: The list of chunks.
        :rtype: list[str]
        """
        raise NotImplementedError

    def __repr__(self):
        return f"{self.__class__.__name__}()"


class Splitter:
    """
    Abstract class for text splitters.

    :param name: The name of the splitter.
    :type name: str, optional
    :param splitters: A dictionary of splitters.
    :type splitters: Dict[str, Any], optional

    :Examples:


    >>> splitter = Splitter(name="markdown")
    >>> splitter.split("# Hello, world!")
    ['<h1>Hello, world!</h1>']

    >>> splitter = Splitter(name="python_code")
    >>> splitter.split("def hello_world():\n    print('Hello, world!')\n")
    ['def hello_world():\n', '    print(', "'Hello, world!'", ')\n']

    """

    def __init__(self, name: str = None, **kwargs) -> None:
        self._name = name
        self._splitter_registry = SplitterRegistry()
        self._kwargs = kwargs

    def split(self, text: str, splitter_name: str = None) -> list[str]:
        """
        Split a text into chunks.

        :param text: The text to split.
        :type text: str
        :return: The list of chunks.
        :rtype: list[str]
        """
        if splitter_name is None:
            splitter_name = self._name

        splitter = self._get_splitter(splitter_name)

        return splitter.split_text(text)

    def split_topics(self, topics: List[Topic]):
        chunks = []
        for topic in topics:
            # TODO: implement filetype_to_splitter
            # TODO(Pouyan): I think we should have a metadata field for filetype
            # TODO(Pouyan): Do you think isn't it bad that split accepts the splitter_name?
            # splitter_name = filetype_to_splitter[topic.metadata['filetype']]
            for chunk in self.split(text=topic.body):
                chunked_topic = Topic(
                    title=topic.title,
                    body=chunk,
                    metadata=topic.metadata,
                )

                chunks.append(chunked_topic.to_dict())
        return chunks

    def _get_splitter(self, splitter_name: str = "character_lc") -> Type[BaseSplitter]:
        """
        Get a splitter by name.
        :param splitter_name: The name of the splitter to get.
        :param **kwargs: Additional keyword arguments to pass to the splitter constructor.
        :raises ValueError: If the splitter name is invalid.
        :return: An instance of the selected splitter.
        """
        splitter_class = self._splitter_registry.get(splitter_name)

        return splitter_class(**self._kwargs)


class CharacterSplitter(BaseSplitter):
    """Split a text into characters."""

    name: ClassVar = "character"

    def split_text(self, text: str) -> list[str]:
        """
        Split a text into characters.

        :param text: The text to split.
        :type text: str
        :return: The list of characters.
        :rtype: list[str]
        """
        return list(text)
