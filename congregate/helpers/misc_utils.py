import os
from requests import get, head
from re import sub, findall
from datetime import timedelta, date


def remove_dupes(my_list):
    """
        Basic deduping function to remove any duplicates from a list
    """
    if len(my_list) > 0:
        new_list = [my_list[0]]
        for e in my_list:
            if e not in new_list:
                new_list.append(e)
        return new_list
    return my_list


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


def expiration_date():
    return (date.today() + timedelta(days=2)).strftime('%Y-%m-%d')


def parse_query_params(params):
    query_params_string = ""
    query_params_list = []
    for p in params:
        if params.get(p, None) is not None:
            query_params_list.append("%s=%s" % (p, str(params[p])))

    if len(query_params_list) > 0:
        query_params_string = "?%s" % "&".join(query_params_list)

    return query_params_string


def get_congregate_path():
    app_path = os.getenv("CONGREGATE_PATH")
    if app_path is None:
        app_path = os.getcwd()
    return app_path
