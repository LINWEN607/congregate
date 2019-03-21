"""
Congregate - GitLab instance migration utility 

Copyright (c) 2018 - GitLab
"""

import requests
import urllib
import json
import sys
import os
from re import sub
from io import BytesIO
import boto3
from botocore.client import Config
try:
    from helpers import conf
except ImportError:
    from congregate.helpers import conf

class aws_client:
    def __init__(self):
        self.config = conf.ig()
        self.s3 = boto3.client('s3', config=Config(signature_version='s3v4'), region_name='us-west-2')

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

    def copy_from_s3_and_import(self, name, namespace, filename):
        file_path = "%s/downloads/%s" % (self.config.filesystem_path, filename)
        self.s3.download_file(self.config.bucket_name, file_path, filename)

        url = '%s/api/v4/projects/import' % (self.config.parent_host)
        data = {
            "path": name,
            "namespace": namespace
        }
        headers = {
            'Private-Token': self.config.parent_token
        }
        with open(file_path, 'r') as f:
            r = requests.post(url, headers=headers, data=data, files={'file': (filename, f)})
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
    
    def copy_file_to_s3(self, key):
        self.s3.upload_file("%s/downloads/%s" % (self.config.filesystem_path, key), self.config.bucket_name, key)
        return True

    def get_s3_keys(self, bucket):
        """Get a list of keys in an S3 bucket."""
        keys = {}
        resp = self.s3.list_objects_v2(Bucket=bucket)
        if resp.get("Contents", None) is not None:
            for obj in resp['Contents']:
                cleaned_key = sub(r'\d{4}-\d{2}-\d{2}_\d{2}-\d{2}-\d{3}_', '', obj['Key'])
                keys[cleaned_key] = obj['Key']
            return keys
        return None