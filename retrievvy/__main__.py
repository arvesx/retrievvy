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

    print(r"           _        _                         ")
    print(r"          | |      (_)                        ")
    print(r"  _ __ ___| |_ _ __ _  _____   ____   ___   _ ")
    print(r" | '__/ _ \ __| '__| |/ _ \ \ / /\ \ / / | | |")
    print(r" | | |  __/ |_| |  | |  __/\ V /  \ V /| |_| |")
    print(r" |_|  \___|\__|_|  |_|\___| \_/    \_/  \__, |")
    print(r"                                         __/ |")
    print(r"                                        |___/ ")

    # Register resource cleanup funcs
    atexit.register(embeddings.shutdown_worker)

    # Start the webserver
    webserver.run()
