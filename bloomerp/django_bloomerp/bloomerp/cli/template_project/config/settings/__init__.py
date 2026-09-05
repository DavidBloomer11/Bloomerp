from pathlib import Path
from bloomerp.cli.project.marketplace_sources import configure_sources
configure_sources(Path(__file__).resolve().parents[2])

import os

from .generated.common import *


_settings_environment = os.environ.get("BLOOMERP_SETTINGS_ENV", "local").lower()
if _settings_environment == "local":
    from .generated.local import *
elif _settings_environment == "production":
    from .generated.production import *
else:
    raise RuntimeError(
        "BLOOMERP_SETTINGS_ENV must be either 'local' or 'production'."
    )

# Project-owned settings load last and are never replaced by scaffold sync.
from .common import *

if _settings_environment == "local":
    from .local import *
else:
    from .production import *

# A pulled generated artifact retains its database's authentication identity.
from .generated.project_manifest import BLOOMERP_PROJECT_MANIFEST
if BLOOMERP_PROJECT_MANIFEST.get("django", {}).get("auth_user_model"):
    AUTH_USER_MODEL = BLOOMERP_PROJECT_MANIFEST["django"]["auth_user_model"]
