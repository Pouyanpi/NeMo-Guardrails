# CoLLM

CoLLM is a framework for creating rails for LLMs. 

## Description 

Rails are specific ways for controlling the output of an LLM e.g. not talk about politics, respond in a specific way to certain user requests, follow a predefine dialog path, use a specific language style, extract data etc. 

Broadly, there are two types of LLM use cases: completion and chat. 

Types of chat rails:
- **Topical**: avoid talking about a specific topic
- **Execution**: execute specific action in specific context
- **Fact Checking**: make sure the response is grounded in a set of facts.
- **Retrieval**: bring additional context for question answering
- **Q&A**: answer certain questions in a specific way;
- **Instruction**: provide natural language instruction for instruction-tuned LLMs
- **Style**: the response should follow specific guide lines.
- **Blacklist**: absolute blacklist for certain words.  

Types of completion rails:
- **Data format**: output should follow a specific format e.g. JSON, possibly with some constraints.

Rails are defined [using YAML](docs/co-yml-format.md). Quick example of topical rails config:

```yaml
user:
  ask about finance:
    - "What stock should I invest in?"
    - "Can you recommend a good strategy to beat the S&P?"
  
bot:  
  explain cant talk about financial advice:
    - "As the official Benefits AI, I cannot provide personalized financial advice or stock recommendations. Stock markets are highly unpredictable and volatile, and investing in stocks carries a certain level of risk."
    
flows:
  - elements:
    - user: ask about finance
    - bot: explain cant provide financial advice
```

See [Rails Reference](docs/rails-reference.md) for more details.

## Installation

```bash
> pip install collm
```

## Usage

To apply rails, you first create a `CompletionRails` or a `ChatRails` instance, configure the desired rails and then use it to interact with the LLM.  

```python

from collm import ChatRails, CompletionRails

config = RailsConfig.from_file("config.yml")

# For completion
app = CompletionRails(config)
app.generate(prompt="Explain the Internet for a 5-year old child.")

# For chat 
app = ChatRails(config)
app.generate(messages=[{
    "role": "user",
    "content": "Hello! What can you do for me?"
}])

```

## Rails configuration

Rails can be configured using YAML, JSON or using the modeling language Colang. 

**TODO**

## Command Line Chat

For testing purposes, the CoLLM framework provides a command line chat that can be used to interact with the LLM. 

```
> collm chat --config=...
```

## Server

An rails server exposes multiple "railed LLM endpoints". Each endpoint can have a different rail configuration.

```
> collm server --config=...

Listening on port 8080.
```

```
POST /{RAIL_CONFIG_ID}/completions
POST /{RAIL_CONFIG_ID}/chat/completions
```

