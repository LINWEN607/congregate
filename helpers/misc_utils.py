from requests import get
from re import sub

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