import os
from pathlib import Path

from starlette.config import Config
from loguru import logger


ENV_PATH = Path(".env")
config = Config(ENV_PATH if ENV_PATH.exists() else None)


# Data
# ----
DATA = Path(config("DATA", default="/app/data"))
DATABASE = DATA / "database.sqlite"
DIR_SPARSE = DATA / "sparse"

# Qdrant
# ------
QDRANT_URL = config("QDRANT_URL", default="http://qdrant:6333")

# Webserver
# ---------
WEB_HOST = config("WEB_HOST", default="0.0.0.0")
WEB_PORT = config("WEB_PORT", cast=int, default=7300)

# Secrets
# -------
WEB_TOKEN = config("WEB_TOKEN", default="")

# Debugging
# ---------
DEBUG = config("DEBUG", cast=bool, default=False)

#
#
# Create dirs ------------------------------
if not DATA.exists():
    DATA.mkdir(parents=True, exist_ok=True)
    logger.info(f"Created data directory at {DATA}")

if not DIR_SPARSE.exists():
    DIR_SPARSE.mkdir(parents=True, exist_ok=True)
    logger.info(f"Created directory at {DIR_SPARSE} to store keyword indexes")
