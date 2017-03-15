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
import configparser
import psycopg2
import pandas as pd
import hashlib
import cr
import os.path

mysql = MySQL()
app = Flask(__name__)
app.secret_key = 'why would I tell you my secret key?'

#conf = configparser.ConfigParser()
#conf.read('config.ini')
#conf.sections()
# MySQL configurations
app.config['MYSQL_DATABASE_USER']= cr.MYSQL_DATABASE_USER
app.config['MYSQL_DATABASE_PASSWORD'] = cr.MYSQL_DATABASE_PASSWORD
app.config['MYSQL_DATABASE_DB'] =  cr.MYSQL_DATABASE_DB
app.config['MYSQL_DATABASE_HOST'] = cr.MYSQL_DATABASE_HOST
mysql.init_app(app)
#app.config.from_pyfile('config.ini', silent=True)





@app.route('/')
def main():
    return render_template('index.html')

@app.route('/redshiftTab')
def redshiftTab():

    con = psycopg2.connect(cr.PSQL_CON_STRING)
    sql = " SELECT table_name FROM information_schema.tables where table_schema = 'public';"
    cur = con.cursor()
    results = []
    cur.execute(sql)
    for record in cur:
        results.append(record[0])
    con.close()
    return render_template('redshift.html',data = results)

    

@app.route('/showSignUp')
def showSignUp():
    return render_template('signup.html')

#@app.route('/get_s3_bucket_list')
def get_s3_bucket_list():
    s3 = boto3.resource('s3',aws_access_key_id = cr.AWS_ACCESS_KEY_ID,aws_secret_access_key = cr.AWS_SECRET_KEY)
    bucket_list = s3.buckets.all()
    result = []
    for bucket in bucket_list:
        if bucket.name.__eq__('elasticbeanstalk-us-west-2-284418807535') == False:
            result.append(bucket.name)
   
    return result
 
def s3_create_bucket(bucket_name):
  
    s3 = boto3.resource('s3',aws_access_key_id = cr.AWS_ACCESS_KEY_ID,aws_secret_access_key = cr.AWS_SECRET_KEY)

    s3.create_bucket(Bucket=bucket_name,CreateBucketConfiguration={'LocationConstraint': 'us-west-1'})
   # return json.dumps(result)

def s3_delete_bucket(bucket_name):
    s3 = boto3.resource('s3',aws_access_key_id = cr.AWS_ACCESS_KEY_ID,aws_secret_access_key = cr.AWS_SECRET_KEY)

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
    bucket.object_versions.delete()
    bucket.delete()

def redshiftTransfer(bucket,key):

    con = psycopg2.connect(cr.PSQL_CON_STRING)
    aws_access_key_id = cr.AWS_ACCESS_KEY_ID
    aws_secret_access_key = cr.AWS_SECRET_KEY
    table_name = bucket.split('.')[0].replace('-','_')
    
    sql2 = """COPY %s from '%s' credentials 'aws_access_key_id=%s;aws_secret_access_key=%s' REGION AS 'us-west-1' delimiter ',' IGNOREHEADER 1;commit"""  % (table_name,'s3://'+bucket+'/'+key,aws_access_key_id,aws_secret_access_key)

    cur = con.cursor()
    cur.execute(sql2)
    con.close()

def to_redshift(bucket):
    s3 = boto3.resource('s3',aws_access_key_id = cr.AWS_ACCESS_KEY_ID,aws_secret_access_key = cr.AWS_SECRET_KEY)

    bucket_name = s3.Bucket(bucket)
    size = sum(1 for _ in bucket_name.objects.all())
    if size > 0:
        con = psycopg2.connect(cr.PSQL_CON_STRING)
        table_name = bucket.split('.')[0]
        table_name = table_name.replace('-','_')
        sql1 = 'truncate'+' '+table_name+';'
        cur = con.cursor()
        cur.execute(sql1)
        con.close()
 
    for key in bucket_name.objects.all():
        redshiftTransfer(bucket,key.key)




@app.route('/send_to_redshift',methods=['POST'])
def send_to_redshift():
    bucket_list = request.form.getlist('input_bucket')

    for bucket in bucket_list:
        to_redshift(bucket)
    return redirect('/S3tab')





@app.route('/s3_delete_bucketList',methods=['POST'])
def s3_delete_bucketList():
    bucket_list = request.form.getlist('input_bucket')
    
    for bucket in bucket_list:
        s3_delete_bucket(bucket)
    return redirect('/S3tab')


def s3_delete_object(bucket_name,object_name):
   
    s3 = boto3.resource('s3',aws_access_key_id = cr.AWS_ACCESS_KEY_ID,aws_secret_access_key = cr.AWS_SECRET_KEY)

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


def convertValue(val):
    return hashlib.sha256(val).hexdigest()


def masktablevalues(table,attributes):
    df = pd.read_csv('/storageData/'+table+'.csv')
    for col in attributes:
        df[col]= df[col].apply(convertValue) 
   
    df.to_csv('/storageData/masked_'+table+'.csv',index = False)
    return 




@app.route('/maskdata',methods=['POST'])
def maskdata():
    attributes = request.form.getlist('input_attributes')
    table = request.form['table_name']
    masktablevalues(table,attributes)
    return redirect('/userHome')


@app.route('/maskattributes/<table_name>')
def maskattributes(table_name):
    script_adr = '/home/ubuntu/flaskapp/storeTable.sh '+table_name
    subprocess.call(script_adr,shell = True)
    con = mysql.connect()
    cursor = con.cursor()
    data = cursor.execute(("select column_name from information_schema.columns where table_name='%s'")% (table_name))
    data = cursor.fetchall()
    return render_template('/mask.html',table_name = table_name,data = data)


@app.route('/s3BucketObjects/<bucketName>')
def s3BucketObjects(bucketName):
    s3 = boto3.resource('s3',aws_access_key_id = cr.AWS_ACCESS_KEY_ID,aws_secret_access_key = cr.AWS_SECRET_KEY)
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
    s3 = boto3.resource('s3',aws_access_key_id = cr.AWS_ACCESS_KEY_ID,aws_secret_access_key = cr.AWS_SECRET_KEY)
    s3.meta.client.upload_file(object_file,bucket_name,object_key)
    script_adr = "/home/ubuntu/flaskapp/removefile.sh "+object_key
    subprocess.call(script_adr,shell = True)


@app.route('/printtablename',methods=['POST'])
def printtablename():
    _tbnames = request.form.getlist('input_table')
   # con = mysql.connect()
   # cursor = con.cursor()
   # cursor.callproc('store_tableData')
   # data = cursor.execute("SELECT * FROM FORMS INTO OUTFILE /storageData/form.csv FIELDS TERMINATED BY , ENCLOSED BY '"' LINES TERMINATED BY \
    bucket_list = get_s3_bucket_list();
   
    for tb_name in _tbnames:
       
        if os.path.isfile("/storageData/"+tb_name+".csv")== False:
       	    script_adr = '/home/ubuntu/flaskapp/storeTable.sh '+tb_name
    	    subprocess.call(script_adr,shell = True)
        exists = False
        for bucket in bucket_list:
            if tb_name.lower() == bucket.split('.')[0].replace('-','_'):
                bucket_name = bucket
                exists = True
                break
        if exists == False:
            bucket_name = tb_name+'.'+str(datetime.date.today())+'.'+str(datetime.datetime.time(datetime.datetime.now()))
            bucket_name = bucket_name.replace('-',':')
            bucket_name = bucket_name.replace(':','.')
            bucket_name = bucket_name.replace('_','-')
            bucket_name = bucket_name.lower()
            s3_create_bucket(bucket_name)
        object_file = "/storageData/masked_"+tb_name+".csv"
        object_key = tb_name+'.csv'

        if os.path.isfile(object_file) == False:
            object_file = "/storageData/"+tb_name+".csv"

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
