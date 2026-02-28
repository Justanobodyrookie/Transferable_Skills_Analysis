import re
import json
import os
import boto3
import mysql.connector
from datetime import datetime
from dotenv import load_dotenv
load_dotenv()


db_config = {
	'host': os.getenv('MYSQL_HOST'),
	'port': os.getenv('MYSQL_PORT'),
	'user': os.getenv('MYSQL_USER'),
	'password': os.getenv('MYSQL_ROOT_PASSWORD'),
	'database': os.getenv('MYSQL_DATABASE')
}
endpoint = os.getenv('MINIO_ENDPOINT')
access_key = os.getenv('MINIO_USER')
secret_key = os.getenv('MINIO_PASSWORD')
bucket_name = 'job-data'
prefix = '2026-02-21/6001001001/'
s3 = boto3.client(
    's3',
    endpoint_url=endpoint,
    aws_access_key_id=access_key,
    aws_secret_access_key=secret_key,
    region_name='us-east-1'
    )
company_list = []
paginator = s3.get_paginator('list_objects_v2')
pages = paginator.paginate(Bucket=bucket_name, Prefix=prefix)
count = 0
conn = None
cursor = None
try:
	conn = mysql.connector.connect(**db_config)
	cursor = conn.cursor()
	jobs_list = []
	sql_insert_company = """insert ignore into company (custNo, name) values (%s, %s)"""
	# --------
	sql_get_company_id = """select custNo, id from company"""
	# --------
	for page in pages:
		if 'Contents' in page:
			for obj in page['Contents']:
				s = obj['Key']
				file = s3.get_object(Bucket=bucket_name, Key=s)
				fi = file['Body'].read().decode('utf-8')
				js_fi = json.loads(fi)
				aa = js_fi['raw_data']
				current_des = aa['description']
				current_tools = []
				if 'pcSkills' in aa:
					for g in aa['pcSkills']:
						h = g['description']
						current_tools.append(h)
				if isinstance(current_tools, list):
					current_tools = ','.join(current_tools)
				else:
					current_tools = str(current_tools)
				if isinstance(current_des, list):
					current_des = ','.join(current_des)
				else:
					current_des = str(current_des)
				eng_wd = re.findall(r'[A-Za-z][A-Za-z0-9+#]*', current_tools)
				eng_wt = re.findall(r'[A-Za-z][A-Za-z0-9+#]*', current_des)
				# --------------------
				job_des = [w.lower() for w in eng_wd]
				job_tools = [a.lower() for a in eng_wt]
				date = datetime.today().strftime('%Y-%m-%d')
				company_no = js_fi['raw_data']['custNo']
				company_name = js_fi['raw_data']['custName']
				region = js_fi['region_code']
				job_code = js_fi['job_code']
				job_name = js_fi['raw_data']['jobName']
				# --------------------
				
				company_list.append((company_no, company_name))
				count = count + 1
				print(f"已處理 {count} 筆")
	cursor.executemany(sql_insert_company, company_list)
	res = cursor.executemany(sql_get_company_id)
	all_company = res.fetchall()
	company_dict = {row[0]: row[1] for row in all_company}
	conn.commit()
	company_list.clear()
	print(f"成功匯入 {cursor.rowcount} 筆資料")
except Exception as e:
	print(f"匯入時發生錯誤: {e}")
finally:
	if conn and conn.is_connected():
		if cursor:
			cursor.close()
		conn.close()
		print(f"成功關閉conn & cursor")