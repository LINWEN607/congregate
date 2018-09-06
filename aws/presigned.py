"""
Congregate - GitLab instance migration utility 

Copyright (c) 2018 - GitLab
"""

import boto3
from botocore.client import Config
import sys
from helpers import conf

s3 = boto3.client('s3', config=Config(signature_version='s3v4'))
conf = conf.ig()

def generate_presigned_url(key, method):
    # Generate the URL to get 'key-name' from 'bucket-name'
    return s3.generate_presigned_url(
        ClientMethod='get_object',
        Params={
            'Bucket': conf.bucket_name,
            'Key': key
        },
        ExpiresIn=240,
        HttpMethod=method
    )

if __name__ == "__main__":
    key = sys.argv[1]
    method = sys.argv[2]
    print generate_presigned_url(key, method)
