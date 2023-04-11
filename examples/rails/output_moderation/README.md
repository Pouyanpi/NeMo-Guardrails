## Output Moderation Rail

This rail allows you to check the if a bot response does not contain harmful content. It takes as input the bot response  returns a boolean value indicating whether the bot response passes moderation or not. This rail is implemented by making a call to the LLM with the question "Is the bot response legal, ethical and not harmful?".

To utilize this rail, you can take a look at the file ```config.co```. The flow defined in the file is as follows

```define flow check bot response
  bot ...
  $allowed = execute output_moderation
  if not $allowed
    bot remove last message
    bot inform answer unknown
```

The ```bot ...``` command is used to indicate that the bot needs to generate a response. The placeholder ```...``` is utilized by the Colang runtime to replacce it with the response from the bot.

The output moderation rail is invoked after a bot response (```bot ...```) using the ```execute output_moderation``` command. This runs the action ```output_moderation``` and returns True if the bot response passes moderation and False otherwise. If the bot response does not pass moderation, we do not display the generated response to the user and instead ask the bot to say that it does not know the answer.

