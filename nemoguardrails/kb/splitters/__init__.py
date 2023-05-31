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


from functools import partial

from langchain.text_splitter import (  # NLTKTextSplitter,; SpacyTextSplitter,
    CharacterTextSplitter,
    LatexTextSplitter,
    MarkdownTextSplitter,
    PythonCodeTextSplitter,
    TextSplitter,
    TokenTextSplitter,
)

text_splitter_kwargs = {
    "chunk_size": 4,
    "chunk_overlap": 0,
}

character_text_splitter_kwargs = {"separator": "\n\n"}

latex_text_splitter_kwargs = {"separator": "\n\n"}

markdown_text_splitter_kwargs = {"separator": "\n\n"}

# nltk_text_splitter_kwargs = {
#      "separator": "\n\n"
# }

# spacy_text_splitter_kwargs = {
#     "separator": "\n\n",
#      "pipeline": "en_core_web_sm",
# }


# CharacterTextSplitter = partial(CharacterTextSplitter, **text_splitter_kwargs)
# LatexTextSplitter = partial(LatexTextSplitter, **latex_text_splitter_kwargs)
# MarkdownTextSplitter = partial(MarkdownTextSplitter, **markdown_text_splitter_kwargs)
# # NLTKTextSplitter = partial(NLTKTextSplitter, **nltk_text_splitter_kwargs)
# # SpacyTextSplitter = partial(SpacyTextSplitter, **spacy_text_splitter_kwargs)
# PythonCodeTextSplitter = partial(PythonCodeTextSplitter, **python_code_text_splitter_kwargs)
# TokenTextSplitter = partial(TokenTextSplitter, **token_text_splitter_kwargs)
# # SentencePieceTextSplitter = partial(SentencePieceTextSplitter, **sentencepiece_text_splitter_kwargs)


SPLITTERS = {
    "character_lc": CharacterTextSplitter,
    "latex_lc": LatexTextSplitter,
    "markdown_lc": MarkdownTextSplitter,
    "text_lc": TextSplitter,
    # "nltk_lc": NLTKTextSplitter,
    # "spacy_lc": SpacyTextSplitter,
    "python_code_lc": PythonCodeTextSplitter,
    "token_lc": TokenTextSplitter,
}


from .registered import RegisteredSplitter, SplitterRegistry
from .splitter import BaseSplitter, Splitter, Topic
