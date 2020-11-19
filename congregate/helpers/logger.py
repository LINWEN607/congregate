from logging import getLogger, FileHandler, StreamHandler, Formatter, Handler, INFO, WARNING

import json
import requests

from congregate.helpers.misc_utils import get_congregate_path

loggers = {}
log_file_format = \
    "[%(asctime)s][%(levelname)s]|%(module)s.%(funcName)s:%(lineno)d| %(message)s"


def myLogger(name):
    global loggers
    app_path = get_congregate_path()
    if loggers.get(name):
        return loggers.get(name)
    else:
        logger = getLogger(name)
        logger.setLevel(INFO)
        file_log_handler = FileHandler(f'{app_path}/data/logs/congregate.log')
        stderr_log_handler = StreamHandler()
        formatter = Formatter(log_file_format, datefmt="%d %b %Y %H:%M:%S")
        file_log_handler.setFormatter(formatter)
        stderr_log_handler.setFormatter(formatter)
        logger.addHandler(file_log_handler)
        logger.addHandler(stderr_log_handler)
        slack_handler = SlackLogHandler()
        slack_handler.setLevel(WARNING)
        logger.addHandler(slack_handler)
        loggers[name] = logger

        return logger


class SlackLogHandler(Handler):
    def __init__(self):
        Handler.__init__(self)

    def emit(self, record):
        try:
            from congregate.helpers.conf import Config
            config = Config()
            if config.slack_url:
                json_data = json.dumps({"text": "{}".format(
                    record.getMessage()), "username": "CongregateBot", "icon_emoji": ":warning:"})
                requests.post(config.slack_url, data=json_data.encode(
                    'ascii'), headers={'Content-Type': 'application/json'})
        except Exception as em:
            print("EXCEPTION: " + str(em))
