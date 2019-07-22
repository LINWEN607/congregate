"""
Honestly not many things I care about in the logging. Format, default level.
"""

import logging
import congregate.helpers.logger as my_log


def test_logger_file_format():
    my_log.log_file_format = \
        "[%(asctime)s][%(levelname)s]|%(module)s.%(funcName)s:%(lineno)d| %(message)s', datefmt='%d %b %Y %H:%M:%S"


def test_logger_default_level():
    log = my_log.myLogger("TEST")
    assert log.level == logging.INFO
