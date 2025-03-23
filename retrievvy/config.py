import os
from pathlib import Path

from starlette.config import Config
from loguru import logger


config = Config(".env")


# Data
# ----
DATA = Path(config("DATA", default=os.getenv("DATA", "/app/data")))
DIR_SPARSE = DATA / "sparse"

# Qdrant
# ------
QDRANT_URL = config("QDRANT_URL", default=os.getenv("QDRANT_URL", "http://qdrant:6333"))

# Webserver
# ---------
WEB_HOST = config("WEB_HOST", default=os.getenv("WEB_HOST", "0.0.0.0"))
WEB_PORT = config("WEB_PORT", cast=int, default=int(os.getenv("WEB_PORT", "7300")))

# Secrets
# -------
WEB_TOKEN = config("WEB_TOKEN", default=os.getenv("WEB_TOKEN", ""))

# Debugging
# ---------
DEBUG = config(
    "DEBUG", cast=bool, default=os.getenv("DEBUG", "false").lower() == "true"
)


#
#
# Create dirs ------------------------------
if not DATA.exists():
    DATA.mkdir(parents=True, exist_ok=True)
    logger.info(f"Created data directory at {DATA}")

if not DIR_SPARSE.exists():
    DIR_SPARSE.mkdir(parents=True, exist_ok=True)
    logger.info(f"Created directory at {DIR_SPARSE} to store keyword indexes")
