import logging


def setup_logging(level: str = "INFO") -> None:
    logging.basicConfig(
        format="%(asctime)s | %(levelname)-8s | %(name)s: %(message)s",
        level=getattr(logging, str(level).upper(), logging.INFO),
    )
    # these two are extremely chatty on DEBUG/INFO, quiet them down a bit
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("telegram").setLevel(logging.WARNING)
