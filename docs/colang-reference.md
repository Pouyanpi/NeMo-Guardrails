# Colang 1.0

This document introduces the version 1.0 of Colang.

Colang is a modeling language enabling the design of rails for conversational systems.

*Rails* are specific ways in which you want to control the behavior of a conversational system (a.k.a. bot) e.g. not talk about politics, respond in a specific way to certain user requests, follow a predefined dialog path, use a specific language style, extract data etc. A rail in colang can be modeled through one or more flows.

## Concepts

- **Utterance**: the raw text coming from the user or the bot
- **Message**: the canonical form (i.e. structured representation) of a user/bot utterance
- **Event**: something that has happened and is relevant to the conversation e.g. user is silent, user clicked something, user made a gesture, etc.
- **Action**: a custom code that the bot can invoke; usually for connection to third-party API
- **Context**: any data relevant to the conversation (i.e. a key-value dictionary)
- **Flow**: a sequence of messages and events, potentially with additional branching logic.

## Syntax

Colang has a "pythonic" syntax in the sense that most constructs resemble their python equivalent and indentation is used as a syntactic element.

### Core Syntax Elements

The core syntax elements are: blocks, statements, expressions, keywords and references (to context variables).

There are three main types of blocks: user message blocks (`define user ...`), flow blocks (`define flow ...`) and bot message blocks (`define bot ...`).

### Keywords Reference

- `bot`: used both when defining a bot message (`define bot ...`) and when using in a flow (`bot ...`)
- `break`: break out of a while loop;
- `continue`: continue to the next iteration of a `while` loop; outside of a loop is similar to `pass` in python;
- `create`: create a new event;
- `define`: used in defining user/bot messages and flows;
- `else`: for `if` and `when` blocks;
- `execute`: for executing actions;
- `event`: for matching an event;
- `flow`: used in defining a flow (`define flow`)
- `goto`: go to the specified label;
- `if`: used in typical `if` block;
- `include`: used to include another `rails` configuration;
- `label`: mark a label in a flow;
- `meta`: provide meta information about a flow;
- `priority`: set the priority of a flow
- `return`: end the current flow;
- `set`: set the content of a context variable;
- `user`: used both when defining a user message (`define user ...`) and when using in a flow (`user ...`)
- `while`: typical `while` loop, similar to python;
- `when`: branching based on the stream of events.

### References

References to context variables always start with a `$` sign e.g. `$name`. All variables are global and accessible in all flows.

Context variables are dynamically typed and they can be:
- boolean
- integer
- float
- string
- list
- dictionary

### Expressions

Expressions can be used to set values for context variables.

Types of supported expressions:
- arithmetic operations
- array indexing using `[...]`
- `len(...)` for arrays and strings
- property accessor using "." for dict objects

### Statements

#### Simple Statements

A simple statement is comprised within a single logical line.

- `bot`: the bot said something.
- `break`: break the current while loop.
- `continue`: goes again to the beginning of the current loop; if no loop, it has no effect.
- `return`: ends the current flow.
- `execute`: executes an action.
- `event`: an event has occurred.
- `goto`: go to a specific label.
- `include`: include another rails configuration.
- `label`: define a label.
- `meta`: define meta information for a flow.
- `set`: set the value of a context variable.
- `user`: the user said something.

#### Compound Statements

Compound statements contain (groups of) other statements;

- `define action`: define an action and its parameters (for documentation purposes).
- `define bot`: define a bot message.
- `define flow`: define a flow.
  - `parallel`: a parallel flow can have multiple parallel instances at the same time;
  - `test`: a test flow is only used for testing
  - `sample`: a sample flow is meant for documentation only
  - `extension`: an extension flow can interrupt other flows on "decision elements"
  - `continuous`: continuous flows cannot be interrupted i.e. they will be aborted if they can't continue.
- `define user`: define examples for a user message.
- `else`: alternative path for `if` / `when`
- `if`: conditional branching.
- `while`: repeated execution.
- `when`: branching based on event.


## Semantics

### User Messages

User message definition blocks define the canonical form message that should be associated with various user utterances e.g.:

```colang
define user express greeting
  "hello"
  "hi"

define user request help
  "I need help with something."
  "I need your help."
```

### Bot Messages

Bot message definition blocks define the utterances that should be associated with various bot message canonical forms:

```colang
define bot express greeting
  "Hello there!"
  "Hi!"

define bot ask wellfare
  "How are you feeling today?"
```

If more than one utterance is specified per bot message, the meaning is that one of them should be chosen randomly.

### Flows

Flows represent how you want the conversation to happen. It includes sequences of user messages, bot messages and potentially other events.


```colang
define flow hello
  user express greeting
  bot express greeting
  bot ask wellfare
```

Additionally, flows can contain additional logic which can be modeled using `if` and `while`.

For example, to alter the greeting message based on whether the user is talking to the bot for the first time or not, we can do the following:

```colang
define flow hello
  user express greeting
  if $first_time_user
    bot express greeting
    bot ask wellfare
  else
    bot expess welcome back
```

The `first_time_user` context variable would have to be set by the host application.

As another example, after asking the user how they feel (`bot ask wellfare`) we can have different paths depending on the user response:

```colang
define flow hello
  user express greeting
  bot express greeting
  bot ask wellfare

  when user express happiness
    bot express happiness
  else when user express sadness
    bot express empathy
```

#### `if` vs. `while`

The `if/else if/else` statement can be used to evaluate expressions involving context variables and alter the flow accordingly. The `when/else when` statement can be used to branch the flow based on next user message/event.


#### Decision priority



### Actions

Actions are custom functions available to be invoked from flows. Action execution can be invoked in a flow using the following syntax:

```colang
define flow ...
  ...
  $result = execute some_action(some_param_1=some_value_1, ...)
```

All action parameters are passed like keyword arguments in python.

### Context

Each conversation is associated with a global context which contains a set of variables and their respective values (key-value pairs). The value for a context variable can be set either directly, or as the return value from an action execution.

```colang
define flow
  ...
  $name = "John"
  $allowed = execute check_if_allowed
```

## Version 1.0 vs. 2.0

Version 2.0 will introduce multiple extensions to 1.0. A non-comprehensive list of language features supported in 2.0 includes:

- `any` element
- sub-flows
- flow parameters and return values
- user messages with entities
- interruption flows
- "..." interruption operator
- snippets
- `for` loop
- conditional bot messages
- contextual user messages
- advanced flows interruption logic
