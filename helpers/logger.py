import logging
import os

class congregate_logger:
    def __init__(self, module_name):
        app_path = os.getenv("CONGREGATE_PATH")
        self.logger = logging.getLogger(module_name)
        self.logger.setLevel(logging.INFO)

        file_log_handler = logging.FileHandler('%s/congregate.log' % app_path)
        stderr_log_handler = logging.StreamHandler()

        formatter = logging.Formatter('[%(asctime)s][%(levelname)s]|%(module)s.%(funcName)s| %(message)s', datefmt='%d %b %Y %H:%M:%S')
        file_log_handler.setFormatter(formatter)
        stderr_log_handler.setFormatter(formatter)

        self.logger.addHandler(file_log_handler)
        self.logger.addHandler(stderr_log_handler)

    

