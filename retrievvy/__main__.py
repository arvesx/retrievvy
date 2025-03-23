import sys
import atexit

from loguru import logger
from retrievvy import database, webserver
from retrievvy.nlp import embeddings

if __name__ == "__main__":
    from retrievvy import config  # has side-effects

    # Initialize resources
    database.init()
    embeddings.start_worker()

    if config.DEBUG:
        logger.remove()
        logger.add(sys.stderr, level="DEBUG")

    # Register resource cleanup funcs
    atexit.register(embeddings.shutdown_worker)

    # Start the webserver
    webserver.run()
