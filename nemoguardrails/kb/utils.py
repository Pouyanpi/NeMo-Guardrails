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

from typing import List

import yaml


def split_markdown_in_topic_chunks(
    content: str, max_chunk_size: int = 400
) -> List[dict]:
    """Splits a markdown content into topic chunks.

    :param content: The markdown content to be split.
    :param max_chunk_size: The maximum size of a chunk.
    """

    chunks = []
    lines = content.strip().split("\n")

    # Meta information for the whole document
    meta = {}

    # If there's a code block at the beginning, with meta data, we parse that first.
    if lines[0].startswith("```"):
        meta_yaml = ""
        lines = lines[1:]
        while not lines[0].startswith("```"):
            meta_yaml += lines[0] + "\n"
            lines = lines[1:]
        lines = lines[1:]

        meta.update(yaml.safe_load(meta_yaml))

    # Every section and subsection title will be part of the title of the chunk.
    chunk_title_parts = []

    # The data for the current chunk.
    chunk_body_lines = []
    chunk_size = 0

    def _record_chunk():
        nonlocal chunk_body_lines, chunk_size

        body = "\n".join(chunk_body_lines).strip()

        # Skip saving if body is empty
        if body:
            chunks.append(
                {
                    "title": " - ".join(chunk_title_parts),
                    "body": body,
                    # We also include the document level meta information
                    **meta,
                }
            )

        chunk_body_lines = []
        chunk_size = 0

    i = 0
    while i < len(lines):
        line = lines[i]

        if line.startswith("#"):
            # If we have a chunk up to this point, we need to record it
            if chunk_body_lines:
                _record_chunk()

            # Update the title parts with the new section/subsection
            level = 0
            while len(line) > 0 and line[0] == "#":
                level += 1
                line = line[1:]

            # Remove all title parts greater than the current level
            chunk_title_parts[level - 1 :] = []
            chunk_title_parts.append(line.strip())

        elif line.strip() == "":
            chunk_body_lines.append("")

            # If the chunk is over the desired size, we reset it
            if chunk_size > max_chunk_size:
                _record_chunk()
        else:
            chunk_body_lines.append(line)
            chunk_size += len(line)

        i += 1

    if chunk_body_lines:
        _record_chunk()

    return chunks


def _identify_document(document: Union[str, bytes]):
    if isinstance(document, bytes):
        return "pdf"
    if document.stript().startswith("<HTML"):
        return "html"
    if document.strip().startswith("#"):
        return "markdown"
    return "txt"



import re

def _kwargs_str_to_kwargs(kwargs_str: str):
  """Converts given `kwargs` as str into kwargs dict."""
  if not kwargs_str:
    return {}
  kwarg_strs = kwargs_str.split(',')
  kwargs = {}
  for kwarg_str in kwarg_strs:
    kwarg_name, kwarg_val = kwarg_str.split('=')
    kwargs[kwarg_name] = _cast_to_pod(kwarg_val)
  return kwargs


def _cast_to_pod(val: str) -> Value:
  """Try cast to bool, int, float, str, in that order."""
  bools = {'True': True, 'False': False}
  if val in bools:
    return bools[val]
  try:
    return int(val)
  except ValueError:
    try:
      return float(val)
    except ValueError:
      return val


def camelcase_to_snakecase(name: str) -> str:
  """Convert camel-case string to snake-case."""
  s1 = _first_cap_re.sub(r'\1_\2', name)
  return _all_cap_re.sub(r'\1_\2', s1).lower()


def snake_to_camelcase(name: str) -> str:
  """Convert snake-case string to camel-case string."""
  return ''.join(n.capitalize() for n in name.split('_'))


def filename_prefix_for_name(name: str) -> str:
  if os.path.basename(name) != name:
    raise ValueError('Should be a dataset name, not a path: %s' % name)
  return camelcase_to_snakecase(name)


def filename_prefix_for_split(name: str, split: str) -> str:
  if os.path.basename(name) != name:
    raise ValueError('Should be a dataset name, not a path: %s' % name)
  return '%s-%s' % (filename_prefix_for_name(name), split)
