from time import sleep
from helpers.logger import myLogger

log = myLogger(__name__)

def stable_retry(function, ExceptionType=Exception,
                 tries=3, delay=5, backoff=1.20):
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