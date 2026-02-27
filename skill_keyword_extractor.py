import json
import re
import boto3
import os
import random
import time
from dotenv import load_dotenv
from collections import Counter


load_dotenv()
endpoint = os.getenv('MINIO_ENDPOINT')
access_key = os.getenv('MINIO_USER')
secret_key = os.getenv('MINIO_PASSWORD')
bucket_name = 'job-data'
prefix = '2026-02-22/6001001008/'
s3 = boto3.client(
    's3',
    endpoint_url=endpoint,
    aws_access_key_id=access_key,
    aws_secret_access_key=secret_key,
    region_name='us-east-1'
    )

response = s3.list_objects_v2(
	Bucket=bucket_name,
	Prefix=prefix
	)
if 'Contents' in response:
	all_keys = [obj['Key'] for obj in response['Contents']]
	
	eng_counter = Counter()
	for s in all_keys:
		file = s3.get_object(
			Bucket=bucket_name,
			Key=s
			)
		fi = file['Body'].read().decode('utf-8')
		js_fi = json.loads(fi)
		aa = js_fi['raw_data']
		current_des = js_fi['raw_data']['description']
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
		result = [w.lower() for w in eng_wd]
		result2 = [a.lower() for a in eng_wt]
		eng_counter.update(result)
		eng_counter.update(result2)
	for word, count in eng_counter.most_common(1000):
		stop = ["https", "http", "www", "com", "tw", "net", "and", "to", "the", "of", "in", "a", "with", "for", "up", "we", "you", "your", "be", "our", "is", "are", "us", "all", "will", "about", "that", "who", "on", "it", "an", "by", "them", "what", "do", "have", "their", "this", "or", "as", "at", "make", "want", "etc", "en", "work", "need", "know", "more", "new", "one", "how", "bellini", "pasta", "worldgym", "pressplay", "haagen", "dazs", "burger"]
		if word not in stop:
			print(f'{word}: {count}') 
else:
	print(f"沒有此路徑，重新檢查")