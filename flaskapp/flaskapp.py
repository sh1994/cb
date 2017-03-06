from flask import Flask, render_template, json, request,redirect,session
from flask.ext.mysql import MySQL
from werkzeug import generate_password_hash, check_password_hash
import json
import subprocess
import os
import sys
import boto3
import datetime
import botocore
import time
mysql = MySQL()
app = Flask(__name__)
app.secret_key = 'why would I tell you my secret key?'

# MySQL configurations
app.config['MYSQL_DATABASE_USER'] = 'cbdemo'
app.config['MYSQL_DATABASE_PASSWORD'] = 'cbdemo13'
app.config['MYSQL_DATABASE_DB'] = 'demodb'
app.config['MYSQL_DATABASE_HOST'] ='cbdemodb.crufheg3upce.us-east-1.rds.amazonaws.com'
mysql.init_app(app)


@app.route('/')
def main():
    return render_template('index.html')

@app.route('/showSignUp')
def showSignUp():
    return render_template('signup.html')

#@app.route('/get_s3_bucket_list')
def get_s3_bucket_list():
    s3 = boto3.resource('s3',aws_access_key_id='AKIAIKSVSR2RH5XADQSA',aws_secret_access_key = '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')
    bucket_list = s3.buckets.all()
    result = []
    for bucket in bucket_list:
        if bucket.name.__eq__('elasticbeanstalk-us-west-2-284418807535') == False:
            result.append(bucket.name)
   
    return result
 
def s3_create_bucket(bucket_name):
    s3 = boto3.resource('s3',aws_access_key_id='AKIAIKSVSR2RH5XADQSA',aws_secret_access_key = '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')
   # s3.create_bucket(bucket_name)
    s3.create_bucket(Bucket=bucket_name,CreateBucketConfiguration={'LocationConstraint': 'us-west-1'})
   # return json.dumps(result)

def s3_delete_bucket(bucket_name):

    s3 = boto3.resource('s3',aws_access_key_id='AKIAIKSVSR2RH5XADQSA',aws_secret_access_key = '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')
    bucket = s3.Bucket(bucket_name)   
    exists = True
    try:
        s3.meta.client.head_bucket(Bucket=bucket_name)
    except botocore.exceptions.ClientError as e:
    # If a client error is thrown, then check that it was a 404 error.
    # If it was a 404 error, then the bucket does not exist.
         error_code = int(e.response['Error']['Code'])
         if error_code == 404:
             exists = False

    for key in bucket.objects.all():
        key.delete()
    #    time.sleep(5)
#    bucket = s3.Bucket(bucket_name)
    bucket.object_versions.delete()
   # time.sleep(50)
    bucket.delete()

@app.route('/s3_delete_bucketList',methods=['POST'])
def s3_delete_bucketList():
    bucket_list = request.form.getlist('input_bucket')
    for bucket in bucket_list:
        s3_delete_bucket(bucket)
    return redirect('/S3tab')


def s3_delete_object(bucket_name,object_name):
    s3 = boto3.resource('s3',aws_access_key_id='AKIAIKSVSR2RH5XADQSA',aws_secret_access_key = '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')
    bucket = s3.Bucket(bucket_name)
    exists = True
    try:
        s3.meta.client.head_bucket(Bucket=bucket_name)
    except botocore.exceptions.ClientError as e:
    # If a client error is thrown, then check that it was a 404 error.
    # If it was a 404 error, then the bucket does not exist.
         error_code = int(e.response['Error']['Code'])
         if error_code == 404:
             exists = False

    for key in bucket.objects.all():
        if key.key.__eq__(object_name)== True:
       	    key.delete()
    #    time.sleep(5)
#    bucket = s3.Bucket(bucket_name)
   # bucket.object_versions.delete()
   # time.sleep(50)
   # bucket.delete()


@app.route('/s3_delete_bucketObject',methods=['POST'])
def s3_delete_bucketObject():
    object_list = request.form.getlist('input_bucket_object')
    bucket_name = request.form['bucket']
   # return bucket_name
    for object in object_list:
        s3_delete_object(bucket_name,object)
    return redirect('/s3BucketObjects/'+bucket_name)

@app.route('/s3BucketObjects/<bucketName>')
def s3BucketObjects(bucketName):
    s3 = boto3.resource('s3',aws_access_key_id='AKIAIKSVSR2RH5XADQSA',aws_secret_access_key = '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')
    bucket = s3.Bucket(bucketName)
    exists = True
    try:
        s3.meta.client.head_bucket(Bucket=bucketName)
    except botocore.exceptions.ClientError as e:
    # If a client error is thrown, then check that it was a 404 error.
    # If it was a 404 error, then the bucket does not exist.
         error_code = int(e.response['Error']['Code'])
         if error_code == 404:
             exists = False
    bucket_objects = []
    for key in bucket.objects.all():
        bucket_objects.append(key.key)

    return render_template('s3BucketObjects.html',bucket = bucketName,bucket_objects = bucket_objects)			

@app.route('/S3tab')
def S3tab():
    bucket_list = get_s3_bucket_list();
    return render_template('s3.html',bucket_list = bucket_list)

@app.route('/showSignin')
def showSignin():
    if session.get('user'):
        return render_template('userHome.html')
    else:
        return render_template('signin.html')

@app.route('/userHome')
def userHome():
    _user = session.get('user')
    if _user:
        con = mysql.connect()
        cursor = con.cursor()
        data = cursor.callproc('demodb_tables')
        data = cursor.fetchall()
#        return data
        return render_template('userHome.html',data = data)
    else:
        return render_template('error.html',error = 'Unauthorized Access')


@app.route('/logout')
def logout():
    session.pop('user',None)
    return redirect('/')

def s3_upload_file(object_file,bucket_name,object_key):
    s3 = boto3.resource('s3',aws_access_key_id='AKIAIKSVSR2RH5XADQSA',aws_secret_access_key = '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')
    s3.meta.client.upload_file(object_file,bucket_name,object_key)

@app.route('/printtablename',methods=['POST'])
def printtablename():
    _tbnames = request.form.getlist('input_table')
   # con = mysql.connect()
   # cursor = con.cursor()
   # cursor.callproc('store_tableData')
   # data = cursor.execute("SELECT * FROM FORMS INTO OUTFILE /storageData/form.csv FIELDS TERMINATED BY , ENCLOSED BY '"' LINES TERMINATED BY \
    for tb_name in _tbnames:
        script_adr = '/home/ubuntu/flaskapp/storeTable.sh '+tb_name
    	subprocess.call(script_adr,shell = True)
        bucket_name = tb_name+'.'+str(datetime.date.today())+'.'+str(datetime.datetime.time(datetime.datetime.now()))
        bucket_name = bucket_name.replace('-',':')
        bucket_name = bucket_name.replace(':','.')
        bucket_name = bucket_name.replace('_','-')
        bucket_name = bucket_name.lower()
        s3_create_bucket(bucket_name)
        object_file = '/storageData/'+tb_name+'.csv'
        object_key = tb_name+'.csv'
        s3_upload_file(object_file,bucket_name,object_key)
 
    return redirect('/userHome')
   # return json.dumps(_tbnames)

@app.route('/validateLogin',methods=['POST'])
def validateLogin():
    try:
        _username = request.form['inputEmail']
        _password = request.form['inputPassword']
        

        if _username == 'root@gmail.com' and  _password == 'root':
	    session['user'] = 'root'
            return redirect('/userHome')
        else:
	    return render_template('error.html',error = 'Wrong Credentials') 
    
        # connect to mysql
           
       # con = mysql.connect()
       # cursor = con.cursor()
       # cursor.callproc('sp_validateLogin',(_username,))
       # data = cursor.fetchall()

        


       
# if len(data) > 0:
       #    if check_password_hash(str(data[0][3]),_password):
       #        session['user'] = data[0][0]
       #         return redirect('/userHome')
       #     else:
       #         return render_template('error.html',error = 'Wrong Email address or Password.')
       # else:
       #     return render_template('error.html',error = 'Wrong Email address or Password.')
            

    except Exception as e:
        return render_template('error.html',error = str(e))
   # finally:
#        cursor.close()
 #       con.close()

   # return 'hello'
@app.route('/signUp',methods=['POST','GET'])
def signUp():
    try:
        _name = request.form['inputName']
        _email = request.form['inputEmail']
        _password = request.form['inputPassword']

        # validate the received values
        if _name and _email and _password:
            
            # All Good, let's call MySQL
            
            conn = mysql.connect()
            cursor = conn.cursor()
            _hashed_password = generate_password_hash(_password)
            cursor.callproc('sp_createUser',(_name,_email,_hashed_password))
            data = cursor.fetchall()

            if len(data) is 0:
                conn.commit()
                return json.dumps({'message':'User created successfully !'})
            else:
                return json.dumps({'error':str(data[0])})
        else:
            return json.dumps({'html':'<span>Enter the required fields</span>'})

    except Exception as e:
        return json.dumps({'error':str(e)})
    finally:
         cursor.close() 
         conn.close()

if __name__ == "__main__":
    app.run(port=5002)
