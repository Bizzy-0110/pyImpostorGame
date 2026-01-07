import logging
import sys

def setup_logger(log_file="server_log.txt"):
    """Configures the server logger to write to file and console."""
    logger = logging.getLogger("ImposterServer")
    logger.setLevel(logging.DEBUG)

    # File Handler
    file_handler = logging.FileHandler(log_file, encoding='utf-8')
    file_handler.setLevel(logging.DEBUG)
    file_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(file_formatter)

    # Console Handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_formatter = logging.Formatter('%(levelname)s: %(message)s')
    console_handler.setFormatter(console_formatter)

    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    return logger

def set_debug_mode(enabled: bool):
    """Updates console logger level based on debug flag."""
    level = logging.DEBUG if enabled else logging.INFO
    for handler in logger.handlers:
        if isinstance(handler, logging.StreamHandler):
            handler.setLevel(level)
    logger.info(f"Debug Mode: {'ON' if enabled else 'OFF'}")

# Global logger instance
logger = setup_logger()
