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


from langchain.text_splitter import (
    CharacterTextSplitter,
    LatexTextSplitter,
    MarkdownTextSplitter,
    # NLTKTextSplitter,
    # SpacyTextSplitter,
    PythonCodeTextSplitter,
    TokenTextSplitter,
    TextSplitter,
    # SentencePieceTextSplitter,
)

from .document_splitter import DocumentSplitter
from .html_parser import HtmlParser
from .markdown_parser import MarkdownParser
from .pdf_parser import PdfParser
from .text_parser import TxtParser
from .splitters.splitter import Splitter

from functools import partial

text_splitter_kwargs = {
    "max_chunk_size": 400,
    "overlap_size": 0,
    "length_function": "len",
}

character_text_splitter_kwargs = {
    "separator": "\n\n"
}


CharacterTextSplitter = partial(CharacterTextSplitter, **character_text_splitter_kwargs)
LatexTextSplitter = partial(LatexTextSplitter, **latex_text_splitter_kwargs)
MarkdownTextSplitter = partial(MarkdownTextSplitter, **markdown_text_splitter_kwargs)
# NLTKTextSplitter = partial(NLTKTextSplitter, **nltk_text_splitter_kwargs)
# SpacyTextSplitter = partial(SpacyTextSplitter, **spacy_text_splitter_kwargs)
PythonCodeTextSplitter = partial(PythonCodeTextSplitter, **python_code_text_splitter_kwargs)
TokenTextSplitter = partial(TokenTextSplitter, **token_text_splitter_kwargs)
# SentencePieceTextSplitter = partial(SentencePieceTextSplitter, **sentencepiece_text_splitter_kwargs)


SPLITTERS = {
    "character": CharacterTextSplitter,
    "latex": LatexTextSplitter,
    "markdown": MarkdownTextSplitter,\
    "text": TextSplitter,
    # "nltk": NLTKTextSplitter,
    # "spacy": SpacyTextSplitter,
    "python_code": PythonCodeTextSplitter,
    "token": TokenTextSplitter,
    # "sentencepiece": SentencePieceTextSplitter,
}



splitters = {
    "markdown": MarkdownParser,
    "html": HtmlParser,
    "txt": TxtParser,
    "pdf": PdfParser,
}
