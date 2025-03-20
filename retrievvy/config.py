from pathlib import Path

from starlette.config import Config
from loguru import logger


config = Config(".env")


# Data
# ----
DATA = Path(config("DATA", default="data"))
DIR_SPARSE = DATA / "sparse"


# Webserver
# ---------
WEB_HOST = config("WEB_HOST")
WEB_PORT = config("WEB_PORT", cast=int)

# Secrets
# -------
WEB_TOKEN = config("WEB_TOKEN")

# Debugging
# ---------
DEBUG = config("DEBUG", cast=bool)


#
#
# Create dirs ------------------------------
if not DATA.exists():
    DATA.mkdir(parents=True, exist_ok=True)
    logger.info(f"Created data directory at {DATA}")

if not DIR_SPARSE.exists():
    DIR_SPARSE.mkdir(parents=True, exist_ok=True)
    logger.info(f"Created directory at {DIR_SPARSE} to store keyword indexes")
