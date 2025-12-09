import logging
import os
import sys

def get_logger(name: str) -> logging.Logger:
    """
    Returns a configured logger instance.
    Logs are written to 'haajar_app.log' and printed to stdout.
    """
    logger = logging.getLogger(name)
    
    # If logger already has handlers, assume it's configured and return it
    if logger.hasHandlers():
        return logger
        
    logger.setLevel(logging.INFO)

    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    # File Handler
    file_handler = logging.FileHandler('haajar_app.log')
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    # Stream Handler (Console)
    stream_handler = logging.StreamHandler(sys.stdout)
    stream_handler.setFormatter(formatter)
    logger.addHandler(stream_handler)

    return logger
