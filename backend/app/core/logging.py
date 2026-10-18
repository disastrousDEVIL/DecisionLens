"""Application logging configuration."""

import logging


def configure_logging(level: str) -> None:
    """Configure concise logs without adding request content or credentials."""
    logging.basicConfig(
        level=level.upper(),
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )
