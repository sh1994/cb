

import boto3

s3 = boto3.resource('s3')
bucket_list = s3.buckets.all()
result = []
for bucket in bucket_list:
    print bucket.name

