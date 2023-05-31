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

import pytest

from . import SPLITTERS
from .registered import RegisteredSplitter, SplitterRegistry, skip_registration


class DummySplitter(RegisteredSplitter):
    name = "dummy_splitter"


@pytest.fixture
def splitter_registry():
    return SplitterRegistry()


def test_init_splitter_registry(splitter_registry):
    assert len(splitter_registry) == len(SPLITTERS)

    assert repr(splitter_registry) == f"SplitterRegistry(splitters={SPLITTERS})"


def test_getitem_splitter(splitter_registry):
    splitter_registry.splitters["dummy_splitter"] = DummySplitter

    assert splitter_registry["dummy_splitter"] == DummySplitter

    with pytest.raises(KeyError):
        _ = splitter_registry["non_existent"]


def test_validate_splitters(splitter_registry):
    class InvalidSplitter(RegisteredSplitter):
        name = "invalid_splitter"

    class ValidSplitter(RegisteredSplitter):
        name = "valid_splitter"

        def split_text(self):
            pass

    splitter_registry.splitters["invalid_splitter"] = InvalidSplitter

    splitter_registry.splitters["valid_splitter"] = ValidSplitter

    with pytest.raises(ValueError):
        splitter_registry.validate_splitters()


def test_contains_splitter(splitter_registry):
    assert "dummy_splitter" in splitter_registry

    assert "non_existent" not in splitter_registry


def test_get_splitter(splitter_registry):
    splitter_registry.splitters["dummy_splitter"] = DummySplitter

    assert splitter_registry.get("dummy_splitter") == DummySplitter

    with pytest.raises(ValueError):
        splitter_registry.get(None)

    with pytest.raises(KeyError):
        splitter_registry.get("non_existent")


def test_registered_splitter_init_subclass():
    class TestSplitter1(RegisteredSplitter):
        pass

    assert TestSplitter1.name == "test_splitter1"

    with pytest.raises(AssertionError):

        class Splitter(RegisteredSplitter):
            __module__ = "__main__"

    with pytest.raises(ValueError):

        class TestSplitter1(RegisteredSplitter):
            pass

    try:

        class TestSplitter1(RegisteredSplitter, skip_registration=True):
            pass

    except Exception:
        pytest.fail(f"Raised {Exception}")


def test_skip_registration(splitter_registry):
    with skip_registration():

        class SkippedSplitter(RegisteredSplitter):
            pass

    assert "skipped_splitter" not in splitter_registry
