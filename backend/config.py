# ============================================================
# APPLICATION CONFIGURATION
# ============================================================

import os

from dotenv import load_dotenv


# ============================================================
# LOAD ENVIRONMENT VARIABLES
# ============================================================

load_dotenv()


# ============================================================
# APPLICATION SETTINGS
# ============================================================

UPLOAD_DIR = os.getenv(
    "UPLOAD_DIR",
    "uploads"
)

DEFAULT_USER_ID = int(
    os.getenv(
        "DEFAULT_USER_ID",
        "1"
    )
)