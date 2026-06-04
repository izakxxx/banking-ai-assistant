import logging

def setup_logging() -> None:
    # Logs en español, como pediste
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    )
