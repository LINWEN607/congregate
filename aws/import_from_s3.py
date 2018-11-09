"""
Congregate - GitLab instance migration utility 

Copyright (c) 2018 - GitLab
"""

import requests
import urllib
import json
import sys
import os
from io import BytesIO
try:
    from helpers import conf
except ImportError:
    from congregate.helpers import conf
    
conf = conf.ig()

def import_from_s3(name, namespace, presigned_url, filename):
    #s3_file = urllib.urlopen(presigned_url)
    with requests.get(presigned_url, stream=True) as r:
        if r.headers["content-type"] != "application/xml":
            url = '%s/api/v4/projects/import' % (conf.parent_host)
            #files = {'file': (filename, r.content)}
            data = {
                "path": name,
                "namespace": namespace
            }
            headers = {
                'Private-Token': conf.parent_token
            }

            r = requests.post(url, headers=headers, data=data, files={'file': (filename, BytesIO(r.content))})
            return r.text
        return None
