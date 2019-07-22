import logging
import os

loggers = {}
log_file_format = \
    "[%(asctime)s][%(levelname)s]|%(module)s.%(funcName)s:%(lineno)d| %(message)s"


def myLogger(name):
    global loggers
    app_path = os.getenv("CONGREGATE_PATH")
    if app_path is None:
        app_path = os.getcwd()
    if loggers.get(name):
        return loggers.get(name)
    else:
        logger = logging.getLogger(name)
        logger.setLevel(logging.INFO)
        file_log_handler = logging.FileHandler('%s/congregate.log' % app_path)
        stderr_log_handler = logging.StreamHandler()

        formatter = logging.Formatter(log_file_format, datefmt="%d %b %Y %H:%M:%S")
        file_log_handler.setFormatter(formatter)
        stderr_log_handler.setFormatter(formatter)
        logger.addHandler(file_log_handler)
        logger.addHandler(stderr_log_handler)
        loggers[name] = logger

        return logger
