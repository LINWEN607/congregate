import boto3
from botocore.client import Config
import sys

s3 = boto3.client('s3', config=Config(signature_version='s3v4'))

bucket = sys.argv[1]
key = sys.argv[2]

# Generate the URL to get 'key-name' from 'bucket-name'
url = s3.generate_presigned_url(
    ClientMethod='get_object',
    Params={
        'Bucket': bucket,
        'Key': key
    }
)

print (url)
