## Fact Checking Rail

This rail allows you to check the factual validity of a bot response. It takes as input the bot response and the retrieved chunks that the bot uses to generate the response. The output is a boolean value indicating whether the bot response is factually valid or not. This rail is implemented as an entailment approach where we make a call to the LLM with the question "Does the bot response entail the retrieved chunks?".

To utilize this rail, you can take a look at the file ```config.co```. The flow defined in the file is as follows

```define flow check facts
  bot ...
  $accurate = execute check_facts
  if not $accurate
    bot remove last message
    bot inform answer unknown
```

The fact checking rail is invoked after a bot response using the ```execute check_facts``` command. This runs the action ```check_facts``` and returns True if the bot response is factually valid and False otherwise. If the bot response is not factually valid, we will not display the generated response to the user and instead ask the bot to say that it does not know the answer.

