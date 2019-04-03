from requests import get
from re import sub
from time import sleep
import logger as log

l = log.congregate_logger(__name__)

def remove_dupes(mylist):
    """
        Basic deduping function to remove any duplicates from a list
    """
    if len(mylist) > 0:
        newlist = [mylist[0]]
        for e in mylist:
            if e not in newlist:
                newlist.append(e)
        return newlist
    return mylist

def download_file(url, path, filename, headers=None):
    # NOTE the stream=True parameter
    r = get(url, stream=True, headers=headers)
    # filename = r.headers["Content-Disposition"].split("=")[1]
    with open("%s/downloads/%s" % (path, filename), 'wb') as f:
        for chunk in r.iter_content(chunk_size=1024): 
            if chunk:
                f.write(chunk)
    return filename

def strip_numbers(s):
    return sub(r"[0-9]+", '', s)

def stable_retry(function, ExceptionType=Exception,
                 tries=3, delay=5, backoff=1.20):
    def f_retry(*args, **kwargs):
        mtries, mdelay = tries, delay
        while mtries > 1:
            try:
                return function(*args, **kwargs)
            except ExceptionType as e:
                l.logger.error(
                    "%s, Api connecion failed Retrying in %d seconds..." %
                    (str(e), mdelay))
                sleep(mdelay)
                mtries -= 1
                mdelay *= backoff
        l.logger.error(
            "Failed to connect to API within {0} Tries".format(tries))
        # return function(*args, **kwargs)
    return f_retry
