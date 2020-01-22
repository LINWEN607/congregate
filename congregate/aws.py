"""
Congregate - GitLab instance migration utility

Copyright (c) 2020 - GitLab
"""

from time import sleep
from subprocess import Popen, PIPE, call
from os import remove, path
from re import sub
from io import BytesIO
import boto3
import requests

from botocore.client import Config
from congregate.helpers.base_class import BaseClass


class AwsClient(BaseClass):
    def __init__(self):
        super(AwsClient, self).__init__()
        self.s3 = boto3.client(
            's3',
            config=Config(
                signature_version='s3v4'),
            region_name=self.config.s3_region)

    def import_from_s3(self, name, namespace, presigned_url, filename, override_params=None):
        retry_count = 0
        url = "{}/api/v4/projects/import".format(self.config.destination_host)
        # Returns out on success, so no need for success tracker
        while True and retry_count <= self.config.max_import_retries:
            sleep_time = self.config.importexport_wait
            try:
                # Added timeout tuple for connection/read until the retry is implemented
                with requests.get(presigned_url, stream=True, timeout=(10, 10)) as r:
                    if r.headers["content-type"] != "application/xml":
                        files = {
                            "file": (filename, BytesIO(r.content))
                        }
                        data = {
                            "path": name.replace(" ", "-"),
                            "namespace": namespace,
                            "name": name
                        }
                        headers = {
                            "Private-Token": self.config.destination_token
                        }
                        if override_params:
                            for k, v in override_params.items():
                                data["override_params[{}]".format(k)] = v

                            r = requests.post(url, headers=headers, data=data, files=files)
                            if r is not None:
                                if r.status_code == 200 or r.status_code == 201:
                                    return r.text
                                elif r.status_code == 400 and str("Name has already been taken") in r.content:
                                    self.log.warn("Project {} already exists".format(name))
                                    return None
                                elif r.status_code == 429:
                                    self.log.warn(
                                        "Too many requests. Getting 429s. Sleeping 30 seconds longer for project: {0}"
                                            .format(name)
                                    )
                                    # Add an additional 30 seconds to the sleep on 429
                                    sleep_time = sleep_time + 30
                                else:
                                    self.log.warn("Project file {0} import post status code was {1} with content {2}".format(
                                        filename,
                                        r.status_code,
                                        r.content)
                                    )
                            else:
                                self.log.warn("Project file {} import post status code was None".format(filename))
            except requests.exceptions.Timeout:
                self.log.error("Project {} import timed out".format(name))
            except requests.exceptions.TooManyRedirects:
                self.log.error("The presigned URL ({}) was bad, please try a different one".format(presigned_url))
            except requests.exceptions.RequestException as e:
                self.log.error("Something went terribly wrong, with error:\n{}".format(e))

            # All paths should fall-thru to here
            sleep(sleep_time)
            retry_count += 1

        # If we hit here, didn't return out with a success
        self.log.error("No import status verified for:\nProject: {0}\nNamespace: {1}\nFile: {2}\nURL: {3}".format(
            name,
            namespace,
            filename,
            url)
        )
        return None

    def get_local_file_path(self, filename):
        file_path = "%s/downloads/%s" % (self.config.filesystem_path, filename)
        # copy from S3 to local machine if it doesn't exist
        if not path.isfile(file_path):
            self.log.info("Copying project file {} from S3 to local machine".format(filename))
            cmd = "aws+--region+{0}+s3+cp+s3://{1}/{2}+{3}".format(
                self.config.s3_region,
                self.config.bucket_name,
                filename,
                file_path)
            call(cmd.split("+"))
        return file_path

    def copy_from_s3_and_import(self, name, namespace, filename):
        file_path = self.get_local_file_path(filename)
        url = "{}/api/v4/projects/import".format(self.config.destination_host)
        data = {
            "path": name.replace(" ", "-"),
            "namespace": namespace,
            "name": name
        }
        headers = {
            "Private-Token": self.config.destination_token
        }
        r = None

        retry_count = 0

        # Returns out on success, so no need for success tracker
        while True and retry_count <= self.config.max_import_retries:
            with open(file_path, 'r') as f:
                self.log.info("Importing project {} from S3".format(name))
                r = requests.post(url, headers=headers, data=data, files={ "file": (filename, f) })

            if r is not None:
                if r.status_code == 200:
                    remove(file_path)
                    return r.text
                else:
                    self.log.warn("Project file {0} import post status code was {1} with content {2}".format(
                        filename,
                        r.status_code,
                        r.content)
                    )
            else:
                self.log.warn("Import post status code was None {0}".format(file_path))

            sleep(15)
            retry_count += 1

        self.log.error("No import status verified for:\nProject: {0}\nNamespace: {1}\nFile: {2}\nFile path: {3}\nURL: {4}".format(
            name,
            namespace,
            filename,
            file_path,
            url)
        )

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

    def is_export_on_aws(self, filename):
        cmd = "aws+--region+{0}+s3+ls+s3://{1}/{2}+--recursive".format(
            self.config.s3_region,
            self.config.bucket_name,
            filename)

        self.log.info("Export status unknown. Looking for file on AWS in region %s location s3://%s/%s", 
                      self.config.s3_region, 
                      self.config.bucket_name, 
                      filename)
        r = Popen(cmd.split("+"), stdout=PIPE)
        return filename in r.stdout.read()

    def set_access_key_id(self, key):
        command = "aws configure set aws_access_key_id {}".format(key)
        call(command.split(" "))

    def set_secret_access_key(self, key):
        command = "aws configure set aws_secret_access_key {}".format(key)
        call(command.split(" "))
