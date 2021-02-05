import logging
from config.conf import LOG_LEVEL


def log_on(app_name):
    logger = logging.getLogger(app_name)
    logger.setLevel(LOG_LEVEL)
    logger.propagate = False
    console_handler = logging.StreamHandler()
    logger.addHandler(console_handler)
    formatter = logging.Formatter(fmt='%(levelname)s:[%(name)s]:%(message)s')
    console_handler.setFormatter(formatter)
    return logger
