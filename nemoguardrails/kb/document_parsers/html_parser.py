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

from bs4 import BeautifulSoup

from .document_parser import DocumentParser


class HtmlParser(DocumentParser):
    """A parser for HTML documents.

    This parser uses BeautifulSoup to parse HTML documents.
    It splits the document into chunks based on the tags in the document.
    Each chunk contains the text of a single tag, along with the tag name as the title.

    Example:
        >>> from nemoguardrails.parsers import HtmlParser
        >>> parser = HtmlParser()
        >>> html_content = "<html><body><h1>My First Heading</h1><p>My first paragraph.</p></body></html>"
        >>> chunks = parser.split_document_in_topic_chunks(html_content)
        >>> for chunk in chunks:
        ...     print(f"Title: {chunk['title']}")
        ...     print(f"Body: {chunk['body']}")
        ...     print("\n---\n")
        Title: h1
        Body: My First Heading
        ---
        Title: p
        Body: My first paragraph.
        ---

    """

    def split_document_in_topic_chunks(
        self, content: str, max_chunk_size: int = 400
    ) -> List[Dict[str, str]]:
        soup = BeautifulSoup(content, "html.parser")
        chunks = []
        for tag in soup.find_all(True):  # find_all(True) will match any tag
            chunks.extend(self._handle_tag(tag, max_chunk_size))

        return chunks

    def _handle_tag(self, tag, max_chunk_size: int) -> List[Dict[str, str]]:
        """Handle an individual HTML tag."""

        # Ignore tags that are just whitespace
        text = tag.get_text().strip()

        title = self._get_title_for_tag(tag)

        if len(text) <= max_chunk_size:
            return [
                {
                    "title": title,
                    "body": text,
                }
            ]

        else:
            # If the text in a tag is too long, split it into smaller chunks

            chunks = []

            for i in range(0, len(text), max_chunk_size):
                chunk_text = text[i : i + max_chunk_size]
                chunks.append(
                    {
                        "title": title,
                        "body": chunk_text,
                    }
                )

            return chunks

    def _get_title_for_tag(self, tag) -> str:
        # Treat heading tags specially
        if tag.name in ["h1", "h2", "h3", "h4", "h5", "h6"]:
            return "Heading: " + tag.get_text().strip()
        # Could add more special treatment for other tags here
        # Else, return the tag name as the title
        else:
            return tag.name


"""
_handle_tag: This method handles the processing of an individual HTML tag. It's responsible for generating one or more chunks from the tag's text, depending on the length of the text and the max_chunk_size.

_get_title_for_tag: This method determines the title for a chunk based on the tag. It treats heading tags (<h1> through <h6>) specially, prepending 'Heading: ' to the tag's text to form the title. For all other tags, it simply uses the tag name as the title.

If you want to give special treatment to other types of tags, you can add more logic to this method. For example, you could prepend 'Paragraph: ' to the text of <p> tags, or 'Link: ' to the text of <a> tags.

The split_document_in_topic_chunks method now just loops over all the tags in the HTML document and calls _handle_tag for each one. This makes the code more modular and easier to understand.
"""
