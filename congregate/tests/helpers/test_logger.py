"""
Honestly not many things I care about in the logging. Format, default level.
"""

import logging
from pytest import mark
import congregate.helpers.logger as my_log

@mark.unit_test
def test_logger_file_format():
    my_log.log_file_format = \
        "[%(asctime)s][%(levelname)s]|%(module)s.%(funcName)s:%(lineno)d| %(message)s', datefmt='%d %b %Y %H:%M:%S"

@mark.unit_test
def test_logger_default_level():
    log = my_log.myLogger("TEST")
    assert log.level == logging.INFO
