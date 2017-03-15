echo $1
tb_name=$1
mysql -u cbdemo -pcbdemo13 demodb --host=cbdemodb.crufheg3upce.us-east-1.rds.amazonaws.com --port=3306 --batch -e "select * from $tb_name"  | sed 's/\t/","/g;s/^/"/;s/$/"/;s/\n//g' > /storageData/$tb_name'.csv'

