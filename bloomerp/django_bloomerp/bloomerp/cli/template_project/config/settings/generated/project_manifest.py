"""Generated from .bloomerp/project.bloomerp.toml by `bloomerp project sync`."""

from bloomerp.config import BloomerpConfig


BLOOMERP_PROJECT_MANIFEST = __PROJECT_MANIFEST__
BLOOMERP_CONFIG = BloomerpConfig.model_validate(
    BLOOMERP_PROJECT_MANIFEST["bloomerp"]
)
