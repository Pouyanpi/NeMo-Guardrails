# Getting Started

This is a getting started guide for users of the very early alpha. This guide will cover:

1. Installation of the Colang Flows framework;
2. Creation of a basic rails application;
3. Using the interactive chat;
4. Calling actions from flows.

## Installation

First, create a folder for your project e.g. `my_assistant`.

```bash
> mkdir my_assistant
> cd my_assistant
```

Create a virtual environment.

```bash
> python3 -m venv venv
```

Activate the virtual environment.

```bash
> source venv/bin/activate
```

Clone the Colang Flows repository.

```bash
> git clone https://gitlab-master.nvidia.com/dialogue-research/colangflows.git
```

or

```bash
> git clone ssh://git@gitlab-master.nvidia.com:12051/dialogue-research/colangflows.git
```

Install the Colang Flows framework from the local repository.

```bash
> pip install -e colangflows
> pip install -r colangflows/requirements.txt
```

If you want to use OpenAI, also install the `openai` package. And make sure that you have the `OPENAI_API_KEY` environment variable set.

```bash
> pip install openai
> export OPENAI_API_KEY=...
```

You should now be able to invoke the `colang` CLI.

```bash
> colangflows --help
```

## Creating a basic rails application

To create a basic LLM rails application, you first need to define the configuration. The recommended way is to create a `config` folder and put all the configuration in there.

Let's create `config/basic.yml` with the following content:

```yaml
models:
  - type: main
    engine: openai
    model: text-davinci-003
```

Alternatively, you can also use a NeMo LLM model.

```yaml
models:
  - type: main
    engine: nemollm
    model: gpt43b
```

## Using the interactive chat

You should now be able to use the interactive chat and talk to the "raw" LLM. The command above will implicitly load the config from the config folder.

```bash
> colangflows chat
```

## Adding instruction rails

To add an instruction rail (i.e. instructions in natural language that the model should follow), add the following to the `config/basic.yml` file:

```yaml
instructions:
  - type: general
    content: |
      Below is a conversation between the official NVIDIA Benefits Ambassador bot and a user.
      The bot is talkative and provides lots of specific details from its context.
      If the bot does not know the answer to a question, it truthfully says it does not know.
```


## ...


## Other examples

For more examples, check out the `colang/examples` folder.
