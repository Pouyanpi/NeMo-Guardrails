# SPDX-FileCopyrightText: Copyright (c) 2026 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
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

"""Private guarded-operation declarations."""

from collections.abc import Callable
from dataclasses import dataclass
from typing import Generic, Protocol, TypeVar

from nemoguardrails.server.experimental._content_checker import GuardedText

PayloadT = TypeVar("PayloadT", contravariant=True)
RequestT = TypeVar("RequestT")
ResponseT = TypeVar("ResponseT")


class GuardedTextProjection(Protocol[PayloadT]):
    """Project one guarded text subject from a provider-owned value."""

    def __call__(self, payload: PayloadT) -> GuardedText: ...


@dataclass(frozen=True, slots=True)
class BufferedGuardedOperation(Generic[RequestT, ResponseT]):
    """Declare the guarded subjects of one buffered provider operation."""

    name: str
    input_projection: GuardedTextProjection[RequestT]
    output_projection: GuardedTextProjection[ResponseT]

    def __post_init__(self) -> None:
        if not isinstance(self.name, str) or not self.name:
            raise ValueError("A guarded operation name must be a non-empty dotted identifier.")
        if not all(part.isidentifier() for part in self.name.split(".")):
            raise ValueError("A guarded operation name must be a non-empty dotted identifier.")
        for label, projection in (
            ("input", self.input_projection),
            ("output", self.output_projection),
        ):
            if not isinstance(projection, Callable):
                raise TypeError(f"The guarded operation {label} projection must be callable.")
