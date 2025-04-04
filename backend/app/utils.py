import logging

def get_logger(name: str = __name__) -> logging.Logger:
    """
    Utility to get a configured logger.
    """
    logger = logging.getLogger(name)
    if not logger.hasHandlers():
        # Set a default handler if no handlers exist
        handler = logging.StreamHandler()
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
    return logger