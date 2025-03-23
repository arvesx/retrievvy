import sys

from loguru import logger
from retrievvy import database, webserver

if __name__ == "__main__":
    from retrievvy import config  # has side-effects

    # Initialize the database
    database.init()

    if config.DEBUG:
        logger.remove()
        logger.add(sys.stderr, level="DEBUG")

    webserver.run()
