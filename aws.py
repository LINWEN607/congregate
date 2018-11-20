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
import boto3
from botocore.client import Config
import sys
try:
    from helpers import conf
except ImportError:
    from congregate.helpers import conf

class aws_client:
    def __init__(self):
        self.config = conf.ig()
        self.s3 = boto3.client('s3', config=Config(signature_version='s3v4'))

    def import_from_s3(self, name, namespace, presigned_url, filename):
        with requests.get(presigned_url, stream=True) as r:
            if r.headers["content-type"] != "application/xml":
                url = '%s/api/v4/projects/import' % (self.config.parent_host)
                data = {
                    "path": name,
                    "namespace": namespace
                }
                headers = {
                    'Private-Token': self.config.parent_token
                }

                r = requests.post(url, headers=headers, data=data, files={'file': (filename, BytesIO(r.content))})
                return r.text
            return None

    def generate_presigned_url(self, key, method):
        # Generate the URL to get 'key-name' from 'bucket-name'
        return self.s3.generate_presigned_url(
            ClientMethod='get_object',
            Params={
                'Bucket': self.config.bucket_name,
                'Key': key
            },
            ExpiresIn=3600,
            HttpMethod=method
        )