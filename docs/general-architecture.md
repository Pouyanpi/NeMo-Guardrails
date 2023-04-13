# General Architecture

The Guardrails toolkit provides a set of tools for adding guardrails to LLM conversational systems. Guardrails (or "rails" for short) represent specific ways for controlling the behavior of a conversational system e.g. not talk about politics, respond in a specific way to certain user requests, follow a predefined dialog path, use a specific language style, extract data in a specific format, not hallucinate facts, etc.

The toolkit includes the following components:

1. Colang: a modeling language for conversational rails configurations.
2. Runtime: a runtime for applying a rails configuration.
3. Python API: `LLMRails` interface
4. Server API: compatible with OpenAI `/chat/completions`
5. Actions server: for running actions in a secure and scalable way
6. Chatbot UI: for quick testing;
7. Integrations with 3rd party frameworks:
   - `RailsChain`
   - `RailsAgent`

The toolkit also provides out-of-the box support for the following types of rails:

1. Topical rails
2. Fact-checking
3. Moderation
4. Hallucination

## Rails Configuration

You can create a rails configuration using a combination of Colang and YAML.

YAML is used to configure some general aspects like what LLM model to use, general instructions for the model and the sample conversation. Everything else is configured through Colang (see [Colang Reference](/docs/colang-reference.md).


## Usage

If you want to integrate guardrails into your existing LLM applications, there are multiple ways.

### Python API

There are two main classes for the python API: `RailsConfig` and `LLMRails`.

```python
from nemo_guardrails import LLMRails, RailsConfig
```

First, you need to create a rails configuration. A rails configuration can be created from a file/folder using `RailsConfig.from_path`, directly from a raw configuration dictionary (`RailsConfig.parse_object`), or from plain YAML + Colang content(`RailsConfig.from_content`).

```python
config = RailsConfig.from_path("path/to/config")
```

Secondly, you need to create an `LLMRails` instance.

```
rails = LLMRails(config)
```

Next, you can start using the rails to interact with LLM using the `generate(...)` method which takes as input an array of user / assistant messages.

```python
messages = [{"role": "user", "content": "Hello! How are you?"}]
result = rails.generate(messages)
```

**NOTE**: the format for the array of messages is the same as for OpenAI API.

#### Sync vs. Async

The `LLMRails` instance provides both a sync and an async interface. For the async interface, you can use `generate_async`:

```python
result = await rails.generate_async(messages)
```

### Use with LangChain

If you are using LangChain, you have two ways to bring guardrails to your app. You can use the `RailsChain` or the `RailsAgent`.
