# Getting Started

This is a getting started guide for users of the very early alpha. This guide will cover:

1. Installation of the CoLLM framework
2. Creation of a basic rails application
3. Using the interactive chat
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

Clone the CoLLM repository.

```bash
> git clone https://gitlab-master.nvidia.com/dialogue-research/collm.git
```

or

```bash
> git clone ssh://git@gitlab-master.nvidia.com:12051/dialogue-research/collm.git
```

Install the CoLLM framework from a local repository.

```bash
> pip install -e collm
> pip install -r collm/requirements.txt
```

If you want to use OpenAI, also install the `openai` package.

```bash
> pip install openai
```

And make sure that you have the `OPENAI_API_KEY` environment variable set.

You should now be able to invoke the `collm` CLI.

```bash
> collm --help
```

## Creating a basic rails application

To create a basic LLM rails application, you first need to define a the configuration. The recommended way is to create a `config` folder and put all the configuration in there.

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

You should now be the interactive chat and basically talk to the "raw" LLM.

```bash
> collm chat
```

The command above will implicitly load the config from the config folder.
