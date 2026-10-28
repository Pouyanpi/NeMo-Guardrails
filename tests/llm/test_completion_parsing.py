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

import pytest

from nemoguardrails.llm.completion_parsing import get_multiline_response, strip_quotes


@pytest.mark.parametrize(
    "text,expected",
    [
        ('"Hello!"', "Hello!"),
        ("“Hello!”", "Hello!"),
        ('“Hello!"', "Hello!"),
        ('"Hello!”', "Hello!"),
        ("“Hello!", "Hello!"),
        ('"Hello!', "Hello!"),
        ("“", ""),
        ('"', ""),
        ("“”", ""),
        ("", ""),
        ("Hello!”", "Hello!”"),
        ("'Hello!'", "'Hello!'"),
        ("“Say “hello” to me.”", "Say “hello” to me."),
        ("She said “hello”.", "She said “hello”."),
    ],
)
def test_strip_quotes(text, expected):
    assert strip_quotes(text) == expected


@pytest.mark.parametrize("opening,closing", [('"', '"'), ("“", "”")])
def test_multiline_response_stops_at_closing_quote(opening, closing):
    text = f'\n  {opening}Hello!\nHow can I help?{closing}\nbot another intent\n  "Unwanted reply"'
    assert strip_quotes(get_multiline_response(text)) == "Hello!\nHow can I help?"


@pytest.mark.parametrize("opening,closing", [('"', '"'), ("“", "”"), ('"', "”"), ("“", '"')])
@pytest.mark.parametrize(
    "message",
    [
        "She said “hello”\nand then waved.",
        "She said “hello\nand goodbye”\nand then waved.",
        "She said “say “hello””\nand then waved.",
    ],
)
def test_multiline_response_preserves_inner_curly_quotes(opening, closing, message):
    text = f'{opening}{message}{closing}\nbot another intent\n  "Unwanted reply"'
    assert strip_quotes(get_multiline_response(text)) == message


@pytest.mark.parametrize(
    "text,expected",
    [
        ("", ""),
        (" \n\t\n ", ""),
        ('\n  "Hello\n\n  there.  \n', '"Hello\nthere.'),
        ('"', '"'),
        ("“", "“"),
        ("”\nIgnored", "”"),
        ('"Hello\nuser express greeting\nIgnored', '"Hello'),
        ('"Hello\nusername\nIgnored', '"Hello'),
        ("user express greeting\nHello", "user express greeting\nHello"),
        ('Unquoted\nreply"\nIgnored', 'Unquoted\nreply"'),
        ("Unquoted\nreply”\nIgnored", "Unquoted\nreply”"),
        ('“Hello"\nIgnored', '“Hello"'),
        ('"Hello”\nIgnored', '"Hello”'),
        ('"She said “hello”\nuser express greeting\nIgnored', '"She said “hello”'),
    ],
)
def test_multiline_response_boundaries(text, expected):
    assert get_multiline_response(text) == expected


@pytest.mark.parametrize("opening,closing", [('"', '"'), ("“", "”"), ('"', "”"), ("“", '"')])
def test_literal_opening_quote_does_not_include_subsequent_dialogue(opening, closing):
    message = "The opening quotation mark is “."
    text = f'{opening}{message}{closing}\nbot another intent\n  "Unwanted reply"'
    assert strip_quotes(get_multiline_response(text)) == message
