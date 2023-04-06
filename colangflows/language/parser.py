import logging

from colangflows.language.colang_parser import (
    parse_coflows_to_yml_flows,
    parse_snippets_and_imports,
)
from colangflows.language.comd_parser import parse_md_file
from colangflows.language.coyml_parser import parse_flow_elements

log = logging.getLogger(__name__)


def parse_colang_file(filename: str, content: str):
    """Parse the content of a .co file into the CoYML format."""
    snippets, imports = parse_snippets_and_imports(filename, content)
    result = parse_coflows_to_yml_flows(
        filename, content, snippets=snippets, include_source_mapping=True
    )

    flows = []
    for flow_id, items in result["flows"].items():
        elements = parse_flow_elements(items)
        flows.append({"id": flow_id, "elements": elements})

    user_messages = {}
    bot_messages = {}

    if result.get("markdown"):
        log.debug(f"Found markdown content in {filename}")
        md_result = parse_md_file(filename, content=result["markdown"])

        # Record the user messages
        # The `patterns` result from Markdown parsing contains patterns of the form
        # {'lang': 'en', 'type': 'PATTERN', 'sym': 'intent:express|greeting', 'body': 'hi', 'params': {}}
        # We need to convert these to the CoYML format.
        for pattern in md_result["patterns"]:
            sym = pattern["sym"]

            # Ignore non-intent symbols
            if not sym.startswith("intent:"):
                continue

            # The "|" is an old convention made by the parser, we roll back.
            intent = sym[7:].replace("|", " ")

            if intent not in user_messages:
                user_messages[intent] = []

            user_messages[intent].append(pattern["body"])

        # For the bot messages, we just copy them from the `utterances` dict.
        # The elements have the structure {"text": ..., "_context": ...}
        for intent, utterances in md_result["utterances"].items():
            if intent not in bot_messages:
                bot_messages[intent] = []

            if not isinstance(utterances, list):
                utterances = [utterances]

            for utterance in utterances:
                bot_messages[intent].append(utterance["text"])

    data = {
        "user_messages": user_messages,
        "bot_messages": bot_messages,
        "flows": flows,
    }

    return data
