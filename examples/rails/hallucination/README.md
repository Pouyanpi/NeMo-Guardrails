## Hallucination Rail

This rail allows checking for bot responses which are prone to hallucination (e.g. responses to questions about persons, medical or legal advice).
Current version is using a self-checking mechanism based on multiple LLM predictions for the same input.
The method is inspired from the SelfCheckGPT paper (https://arxiv.org/abs/2303.08896), but is using an LLM call to check for consistency or agreement between the different predictions.


The output is a boolean value indicating whether the bot response is prone to be a hallucination.
This rail is implemented using self-checking for consistency / agreement between the bot response and **n** other completions  (in current version, **n=2**) for the same input.
The other completions are generated with a single extra LLM call, with a higher temperature, and using beam search to get all completions in a single call.
Having the original bot response and a context consisting of the other completions, we are looking for agreement between them:
"Is the bot response in agreement with the context?".

To utilize this rail, you can take a look at the file ```config.co```. The flow defined in the file is as follows

```define flow check hallucination
  bot ...
  $result = execute check_hallucination
  if $result
     bot inform answer prone to hallucination
```

The ```bot ...``` command is used to match any bot response. The wildcard ```...``` is utilized by the Colang runtime to replace it with the response from the bot.

The hallucination rail is invoked after a bot response using the ```execute check_hallucination``` command. This runs the action ```check_hallucination``` and returns True if there is the bot response is prone to hallucination and False otherwise.
If the above flow, if bot response is prone to be a hallucination, the bot will respond with a message informing the user about double-checking the information in the last bot message.
