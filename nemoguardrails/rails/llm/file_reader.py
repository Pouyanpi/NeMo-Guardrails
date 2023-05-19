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

import yaml

__all__ = [
    "file_reader",
]


class Reader(ABC):
    @abstractmethod
    def load(self, file_path):
        pass


class GenericFileReader(Reader):
    extensions = [".html", "txt", "md", "co"]

    def load(self, file_path):
        with open(file_path, "r") as f:
            return f.read()


class YAMLReader(Reader):
    extensions = ["yaml", "yml"]

    def load(self, file_path):
        with open(file_path, "r") as f:
            return yaml.safe_load(f.read())


class ReaderFactory:
    readers = {
        "extension": Reader(),
    }

    @classmethod
    def get(cls, file_extension):
        for file_extension in GenericFileReader.extensions:
            return GenericFileReader()

        for file_extension in YAMLReader.extensions:
            return YAMLReader()

        reader = cls.readers.get(file_extension)

        if not reader:
            raise ValueError(
                f"No parser available for the file extension: {file_extension}"
            )

        return reader


file_reader = ReaderFactory().get
