import traceback

from time import sleep
from functools import wraps
from congregate.helpers.logger import myLogger
from congregate.helpers.exceptions import ConfigurationException

log = myLogger(__name__)


def stable_retry(function, ExceptionType=Exception, delay=5, backoff=1.20):
    @wraps(function)
    def f_retry(*args, **kwargs):
        from congregate.helpers.base_class import BaseClass
        b = BaseClass()
        retries = b.config.max_import_retries
        mretries, mdelay = retries, delay
        while mretries >= 0:
            try:
                return function(*args, **kwargs)
            except ConfigurationException:
                return function(*args, **kwargs)
            except ExceptionType as e:
                log.error(
                    "{0}, Api connecion failed Retrying in {1} seconds...".format(e, mdelay))
                log.error(traceback.print_exc)
                sleep(mdelay)
                mretries -= 1
                mdelay *= backoff
        log.error("Failed to connect to API within {0} retr{1}".format(
            retries, "y" if retries else "ies"))
    return f_retry


def configurable_stable_retry(ExceptionType=Exception, retries=3, delay=5, backoff=1.20):
    def stable_retry(function, ExceptionType=ExceptionType,
                     retries=retries, delay=delay, backoff=backoff):
        def f_retry(*args, **kwargs):
            mretries, mdelay = retries, delay
            while mretries >= 0:
                try:
                    return function(*args, **kwargs)
                except ExceptionType as e:
                    log.error(
                        "{0}, Api connecion failed Retrying in {1} seconds...".format(e, mdelay))
                    sleep(mdelay)
                    mretries -= 1
                    mdelay *= backoff
            log.error("Failed to connect to API within {0} retr{1}".format(
                retries, "y" if retries else "ies"))
            log.error(traceback.print_exc)
        return f_retry
    return stable_retry
