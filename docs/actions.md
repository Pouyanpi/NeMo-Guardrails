# Actions

Actions are a key component of the Colang Flows framework.


## Special parameters

The following parameters are special and are provided by the Colang Flows framework, if they appear in the signature of an action:

- `events`: the history of events so far; the last one is the one triggering the action itself.
- `context`: the context data available to the action;
- `llm`: access to the LLM instance (BaseLLM from LangChain)


## Included actions

The following actions are included in the Colang Flows framework:

### Wolfram Alpha

The `wolfram_alpha_request` action can be used to query Wolfram Alpha.

The `WOLFRAM_ALPHA_APP_ID` must be set to a valid Wolfram Alpha app ID.
