# Rails


## Chat Rails

### Topical

Avoid talking about a specific topic.


### Execution

Execute specific action in specific context.


### Fact Checking

Make sure the response is grounded in a set of facts.


### Context
Bring additional context for question answering.


### Q&A

Answer certain questions in a specific way.

### Instruction

Provide natural language instruction for instruction-tuned LLMs.

### Style
The response should follow specific guide lines.



## Completion Rails

### Hallucination
Identify messages which are prone to hallucination.
Current version is using a self-checking mechanism based on multiple LLM predictions for the same input.

### Data format

Output should follow a specific format e.g. JSON, possibly with some constraints.

See [https://github.com/shreyar/guardrails](https://github.com/shreyar/guardrails).

### Toxicity filter

Remove any message with a toxicity below a specific threshold.
