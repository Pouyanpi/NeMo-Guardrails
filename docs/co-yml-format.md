# CoYML Rails format

Rails can be configured using YAML. 

Quick example:

```yaml
# Canonical user messages
user:
  ask about politics:
    - "Who should I vote with?"
    - "What do you think about the president of US?"
  
  ask about finance:
    - "What stock should I invest in?"
    - "Can you recommend a good strategy to beat the S&P?"
  
  ask about food:
    - "Can you recommend a good place to eat?"
    
  ask math question:
    - "What is the square root of 5?"
    - "How much is 123 * 768?"
    

# Canonical bot messages
bot:
  explain information missing: 
    - "I'm sorry, but I don't have that information. However, you can try searching online or consulting an encyclopedia for more accurate answers."
  
  explain cant provide financial advice:
    - "As the official Benefits AI, I cannot provide personalized financial advice or stock recommendations. Stock markets are highly unpredictable and volatile, and investing in stocks carries a certain level of risk."


# Flows
flows:
  - elements:
      - user: ask about politics
      - bot: explain cant talk about politics
        
  - elements:
      - user: ask about finance
      - bot: explain cant provide financial advice

  - id: answer math questions using wolfram
    elements:
      - user: ask math question
      - execute: wolfram alpha request
      - bot: respond with result

# Instructions
instructions:
  - type: general
    content: |
      Below is a conversation between the official Benefits AI bot and a user.
      The bot is talkative and provides lots of specific details from its context. 
      If the bot does not know the answer to a question, it truthfully says it does not know.
   

```