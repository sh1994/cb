import boto3
import botocore

s3 = boto3.resource('s3')

s3.create_bucket(Bucket='bucketcloudbot.1245')
s3.create_bucket(Bucket='bucketcloudbot.1245', CreateBucketConfiguration={
'LocationConstraint': 'us-west-1'})
