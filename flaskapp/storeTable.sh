echo $1
tb_name=$1
mysql -u  -p  --host= --port= --batch -e "select * from $tb_name"  | sed 's/\t/","/g;s/^/"/;s/$/"/;s/\n//g' > /storageData/$tb_name'.csv'

