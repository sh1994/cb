import boto3
s3 = boto3.resource('s3')
s3.Object('cloudbotnew', 'hello.txt').put(Body=open('/tmp/hello.txt', 'rb'))
