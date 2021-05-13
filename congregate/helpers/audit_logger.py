import logging

loggers = {}
log_file_format = \
    "[%(asctime)s][%(levelname)s]| %(message)s"


def audit_logger(name, app_path='.'):
    name = name + "_audit"
    global loggers
    if loggers.get(name):
        return loggers.get(name)
    else:
        logger = logging.getLogger(name)
        logger.setLevel(logging.INFO)
        file_log_handler = logging.FileHandler(
            f'{app_path}/data/logs/audit.log')
        stderr_log_handler = logging.StreamHandler()

        formatter = logging.Formatter(
            log_file_format, datefmt="%d %b %Y %H:%M:%S")
        file_log_handler.setFormatter(formatter)
        stderr_log_handler.setFormatter(formatter)
        logger.addHandler(file_log_handler)
        logger.addHandler(stderr_log_handler)
        loggers[name] = logger

        return logger
