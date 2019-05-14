"""
Congregate - GitLab instance migration utility

Copyright (c) 2018 - GitLab
"""

import requests
from os import remove, path
import subprocess
from re import sub
from io import BytesIO
import boto3
from botocore.client import Config
from helpers.base_class import BaseClass
import json


class AwsClient(BaseClass):
    def __init__(self):
        super(AwsClient, self).__init__()
        self.s3 = boto3.client(
            's3',
            config=Config(
                signature_version='s3v4'),
            region_name=self.config.s3_region)

    def import_from_s3(self, name, namespace, presigned_url, filename, override_params=None):
        with requests.get(presigned_url, stream=True) as r:
            if r.headers["content-type"] != "application/xml":
                url = '%s/api/v4/projects/import' % (self.config.parent_host)
                data = {
                    "path": name.replace(" ", "-"),
                    "namespace": namespace
                }
                headers = {
                    'Private-Token': self.config.parent_token
                }
                if override_params is not None:
                    r = requests.post(url, headers=headers, params="&".join(override_params), data=data, files={
                        'file': (filename, BytesIO(r.content))})
                else:
                    r = requests.post(url, headers=headers, data=data, files={
                        'file': (filename, BytesIO(r.content))})
                return r.text
            self.log.error(r.text)
            return None

    def copy_from_s3_and_import(self, name, namespace, filename):
        file_path = "%s/downloads/%s" % (self.config.filesystem_path, filename)
        if not path.isfile(file_path):
            self.log.info("Copying %s to local machine" % filename)
            cmd = "aws+s3+cp+s3://%s/%s+%s" % (
                self.config.bucket_name, filename, file_path)
            subprocess.call(cmd.split("+"))

        url = '%s/api/v4/projects/import' % (self.config.parent_host)
        data = {
            "path": name.replace(" ", "-"),
            "namespace": namespace
        }
        headers = {
            'Private-Token': self.config.parent_token
        }
        r = None
        with open(file_path, 'r') as f:
            self.log.info("Importing %s" % name)
            r = requests.post(
                url,
                headers=headers,
                data=data,
                files={
                    'file': (
                        filename,
                        f)})

        if r is not None:
            remove(file_path)
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

    def copy_file_to_s3(self, filename):
        key = sub(r'\d{4}-\d{2}-\d{2}_\d{2}-\d{2}-\d{3}_', '', filename)
        key = key.replace("_export", "")
        self.s3.upload_file(
            "%s/downloads/%s" %
            (self.config.filesystem_path,
             filename),
            self.config.bucket_name,
            key)
        return True

    def get_s3_keys(self, bucket):
        """Get a list of keys in an S3 bucket."""
        keys = {}
        paginator = self.s3.get_paginator('list_objects_v2')
        page_iterator = paginator.paginate(Bucket=bucket)
        page_count = 1
        for page in page_iterator:
            # print "page: %d" % page_count
            for obj in page['Contents']:
                cleaned_key = sub(
                    r'\d{4}-\d{2}-\d{2}_\d{2}-\d{2}-\d{3}_',
                    '',
                    obj['Key']).lower()
                keys[cleaned_key] = obj['Key']
            page_count += 1
        return keys
