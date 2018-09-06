"""
Congregate - GitLab instance migration utility 

Copyright (c) 2018 - GitLab
"""

import requests
import urllib
import json
import sys
import os
from helpers import conf

conf = conf.ig()

def import_from_s3(name, namespace, presigned_url):
    s3_file = urllib.urlopen(presigned_url)
    if s3_file.info().type != "application/xml":
        url =  '%s/api/v4/projects/import' % (conf.parent_host)
        files = {'file': s3_file}
        data = {
            "path": name,
            "namespace": namespace
        }
        headers = {
            'Private-Token': conf.parent_token
        }

        r = requests.post(url, headers=headers, data=data, files=files)
        return r.text
    return None
