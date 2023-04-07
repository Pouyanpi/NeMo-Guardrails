import os

from colangflows.rails import RailsConfig
from tests.utils import TestChat

CONFIGS_FOLDER = os.path.join(os.path.dirname(__file__), "..", "examples", "rails")


def test_general():
    config = RailsConfig.from_path(os.path.join(CONFIGS_FOLDER, "general"))
    chat = TestChat(
        config,
        llm_completions=[
            "Hello! How can I help you today?",
            "The game of chess was invented by a man named Chaturanga.",
        ],
    )

    chat.user("Hello! How are you?")
    chat.bot("Hello! How can I help you today?")

    chat.user("Who invented the game of chess?")
    chat.bot("The game of chess was invented by a man named Chaturanga.")


def test_game():
    config = RailsConfig.from_path(os.path.join(CONFIGS_FOLDER, "game"))
    chat = TestChat(
        config,
        llm_completions=[
            "  express greeting",
            "  ask about work",
            "  express agreement",
            "bot express thank you",
            '  "Thank you!"',
        ],
    )

    chat.user("hi")
    chat.bot("Got some good pieces out here, if you're looking to buy. More inside.")

    chat.user("Do you work all day here?")
    chat.bot(
        "Aye, that I do. I've got to, if I hope to be as good as Eorlund Gray-Mane some day. "
        "In fact, I just finished my best piece of work. It's a sword. "
        "I made it for the Jarl, Balgruuf the Greater. It's a surprise, and "
        "I don't even know if he'll accept it. But...\n"
        "Listen, could you take the sword to my father, Proventus Avenicci? "
        "He's the Jarl's steward. He'll know the right time to present it to him."
    )

    chat.user("sure")
    chat.bot("Thank you!")
