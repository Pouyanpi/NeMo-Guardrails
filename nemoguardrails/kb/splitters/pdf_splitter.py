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

from io import BytesIO
from typing import Dict, List

import PyPDF2

from .splitter import BaseSplitter


class PdfSplitter(BaseSplitter):
    def split(
        self, content: str, max_chunk_size: int = 400
    ) -> List[Dict[str, str]]:
        # Read the PDF file
        # pip install PyPDF2
        pdf_file_obj = BytesIO(content)
        pdf_reader = PyPDF2.PdfFileReader(pdf_file_obj)
        chunks = []

        for page_num in range(pdf_reader.getNumPages()):
            page_obj = pdf_reader.getPage(page_num)
            page_text = page_obj.extract_text()
            # Split the page's text into chunks

            for i in range(0, len(page_text), max_chunk_size):
                chunk_text = page_text[i : i + max_chunk_size]

                chunks.append(
                    {
                        "title": f"Page {page_num+1}",
                        "body": chunk_text,
                    }
                )

        return chunks
