from __future__ import annotations

import logging

from app.core.config import Settings


def configure_logging(settings: Settings) -> None:
    level = logging.INFO if settings.app_env != "dev" else logging.DEBUG
    logging.basicConfig(
        level=level,
        format="%(asctime)s %(levelname)s %(name)s - %(message)s",
    )
