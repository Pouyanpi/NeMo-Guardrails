# Rails config

Below are the elements that should be configured using YAML:

```yaml

# Instructions
instructions:
  - type: general
    content: |
      Below is a conversation between the official Benefits AI bot and a user.
      The bot is talkative and provides lots of specific details from its context.
      If the bot does not know the answer to a question, it truthfully says it does not know.

# Models
models:
  - type: main
    engine: openai
    model: text-davinci-003

```
