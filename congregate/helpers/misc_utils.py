from requests import get, head
from re import sub, findall
from time import sleep


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


def download_file(url, path, filename=None, headers=None):
    # NOTE the stream=True parameter
    if __is_downloadable(url):
        r = get(url, stream=True, headers=headers, allow_redirects=True)
        if filename is None:
            filename = __get_filename_from_cd(r.headers.get('content-disposition'))
        with open("%s/downloads/%s" % (path, filename), 'wb') as f:
            for chunk in r.iter_content(chunk_size=1024):
                if chunk:
                    f.write(chunk)
    return filename


def __is_downloadable(url):
    """
        Does the url contain a downloadable resource
    """
    h = head(url, allow_redirects=True)
    header = h.headers
    content_type = header.get('content-type')
    if 'text' in content_type.lower():
        return False
    if 'html' in content_type.lower():
        return False
    return True


def __get_filename_from_cd(cd):
    """
        Get filename from content-disposition
    """
    if not cd:
        return None
    fname = findall('filename=(.+)', cd)
    if len(fname) == 0:
        return None
    return fname[0]


def strip_numbers(s):
    return sub(r"[0-9]+", '', s)