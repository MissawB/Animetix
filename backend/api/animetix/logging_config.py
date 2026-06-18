import logging

# Centralized logging configuration for the backend
LOG_FORMAT = "[%(asctime)s] %(levelname)s %(name)s:%(lineno)d - %(message)s"
logging.basicConfig(level=logging.INFO, format=LOG_FORMAT)


def get_logger(name: str = __name__) -> logging.Logger:
    """Return a logger with the given name.

    This helper ensures all modules use the same configuration.
    """
    return logging.getLogger(name)
