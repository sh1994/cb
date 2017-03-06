import boto3
import os.path
import sys
import os
import glob
#from boto3.s3.key import Key
s3= boto3.connect_s3()
bucket =s3.get_bucket(bucketcloudbot)
for key in bucket.list():
	key.delete()
s3.delete_bucket(bucketcloudbot)


