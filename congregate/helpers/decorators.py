from time import sleep
from congregate.helpers.logger import myLogger
from congregate.helpers.exceptions import ConfigurationException
from congregate.helpers.logger import myLogger
from functools import wraps

log = myLogger(__name__)


def stable_retry(function, ExceptionType=Exception,
                 tries=3, delay=5, backoff=1.20):
    @wraps(function)
    def f_retry(*args, **kwargs):
        mtries, mdelay = tries, delay
        while mtries > 1:
            try:
                return function(*args, **kwargs)
            except ConfigurationException:
                return function(*args, **kwargs)
            except ExceptionType as e:
                log.error(
                    "%s, Api connecion failed Retrying in %d seconds..." %
                    (str(e), mdelay))
                sleep(mdelay)
                mtries -= 1
                mdelay *= backoff
        log.error(
            "Failed to connect to API within {0} Tries".format(tries))
        # return function(*args, **kwargs)
    return f_retry

def configurable_stable_retry(ExceptionType=Exception,
                 tries=3, delay=5, backoff=1.20):
    def stable_retry(function, ExceptionType=ExceptionType,
                 tries=tries, delay=delay, backoff=backoff):
        def f_retry(*args, **kwargs):
            mtries, mdelay = tries, delay
            while mtries > 1:
                try:
                    return function(*args, **kwargs)
                except ExceptionType as e:
                    log.error(
                        "%s, Api connecion failed Retrying in %d seconds..." %
                        (str(e), mdelay))
                    sleep(mdelay)
                    mtries -= 1
                    mdelay *= backoff
            log.error(
                "Failed to connect to API within {0} Tries".format(tries))
            # return function(*args, **kwargs)
        return f_retry
    return stable_retry