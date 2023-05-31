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

from typing import Dict, List

from .document_splitter import BaseSplitter


class TextSplitter(BaseSplitter):
    def split(self, content: str, max_chunk_size: int = 400) -> List[Dict[str, str]]:
        chunks = []

        for i in range(0, len(content), max_chunk_size):
            chunk_text = content[i : i + max_chunk_size]

            chunks.append(
                {
                    "title": f"Text Chunk {i}",
                    "body": chunk_text,
                }
            )

        return chunks
