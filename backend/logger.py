import logging
import sys

# Configure logging format
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

def setup_logger(name: str):
    """Setup a logger with the given name."""
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)
    
    # Check if handler already exists to avoid duplicate logs during reload
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(logging.Formatter(LOG_FORMAT))
        logger.addHandler(handler)
        
    return logger

# Create a default logger for the app
logger = setup_logger("rag_app")
