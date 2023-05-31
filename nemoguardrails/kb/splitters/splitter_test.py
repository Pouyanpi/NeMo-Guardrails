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
from typing import Dict

import pytest

from .splitter import Splitter, Topic


# testing Topic class
def test_topic_class():
    # normal case
    metadata: Dict[str, str] = {"filetype": "txt"}
    topic = Topic(title="Test", body="This is a test", metadata=metadata)

    assert topic.title == "Test"
    assert topic.body == "This is a test"
    assert topic.metadata == metadata

    # case with no metadata
    topic = Topic(title="Test", body="This is a test")

    assert topic.title == "Test"
    assert topic.body == "This is a test"
    assert topic.metadata == {}


def test_splitter_class():
    splitter = Splitter(
        name="character_lc", separator="", chunk_size=1, chunk_overlap=0
    )
    # normal case
    assert splitter.split("Test") == ["T", "e", "s", "t"]

    # case with no name passed to splitter, this should raise an error
    with pytest.raises(ValueError):
        splitter = Splitter()

    with pytest.raises(KeyError, match=r"does not exist in the registry"):
        splitter = Splitter(name="not_a_registered_splitter")

    # case with topics splitting
    metadata: Dict[str, str] = {"filetype": "txt"}
    topic1 = Topic(title="Test1", body="This is a test1", metadata=metadata)
    topic2 = Topic(title="Test2", body="This is a test2", metadata=metadata)
    topics = [topic1, topic2]

    result = splitter.split_topics(topics)

    assert result == [
        {"title": "Test1", "body": "T", "metadata": {"filetype": "txt"}},
        {"title": "Test1", "body": "h", "metadata": {"filetype": "txt"}},
        {"title": "Test1", "body": "i", "metadata": {"filetype": "txt"}},
        {"title": "Test1", "body": "s", "metadata": {"filetype": "txt"}},
        {"title": "Test1", "body": "i", "metadata": {"filetype": "txt"}},
        {"title": "Test1", "body": "s", "metadata": {"filetype": "txt"}},
        {"title": "Test1", "body": "a", "metadata": {"filetype": "txt"}},
        {"title": "Test1", "body": "t", "metadata": {"filetype": "txt"}},
        {"title": "Test1", "body": "e", "metadata": {"filetype": "txt"}},
        {"title": "Test1", "body": "s", "metadata": {"filetype": "txt"}},
        {"title": "Test1", "body": "t", "metadata": {"filetype": "txt"}},
        {"title": "Test1", "body": "1", "metadata": {"filetype": "txt"}},
        {"title": "Test2", "body": "T", "metadata": {"filetype": "txt"}},
        {"title": "Test2", "body": "h", "metadata": {"filetype": "txt"}},
        {"title": "Test2", "body": "i", "metadata": {"filetype": "txt"}},
        {"title": "Test2", "body": "s", "metadata": {"filetype": "txt"}},
        {"title": "Test2", "body": "i", "metadata": {"filetype": "txt"}},
        {"title": "Test2", "body": "s", "metadata": {"filetype": "txt"}},
        {"title": "Test2", "body": "a", "metadata": {"filetype": "txt"}},
        {"title": "Test2", "body": "t", "metadata": {"filetype": "txt"}},
        {"title": "Test2", "body": "e", "metadata": {"filetype": "txt"}},
        {"title": "Test2", "body": "s", "metadata": {"filetype": "txt"}},
        {"title": "Test2", "body": "t", "metadata": {"filetype": "txt"}},
        {"title": "Test2", "body": "2", "metadata": {"filetype": "txt"}},
    ]
