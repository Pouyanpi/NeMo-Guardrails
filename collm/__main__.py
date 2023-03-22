import logging

from collm.cli import app

if __name__ == "__main__":
    # Set the default logging level to INFO
    logging.basicConfig(level=logging.WARNING)

    app()
