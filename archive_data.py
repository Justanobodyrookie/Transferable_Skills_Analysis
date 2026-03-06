import os
import boto3
import tarfile
import io
from datetime import datetime
from dotenv import load_dotenv
n = datetime.now()
month = n.strftime('%Y-%m')
load_dotenv()
endpoint = os.getenv('MINIO_ENDPOINT')
access_key = os.getenv('MINIO_USER')
secret_key = os.getenv('MINIO_PASSWORD')
s3 = boto3.client(
    's3',
    endpoint_url=endpoint,
    aws_access_key_id=access_key,
    aws_secret_access_key=secret_key,
    region_name='us-east-1'
    )
bucket_name = 'job-data'
target_prefix = ''
output_filename = ''

def archive():
	all_keys = []
	paginator = s3.get_paginator('list_objects_v2')
	pages = paginator.paginate(Bucket=bucket_name)
	for page in pages:
		if 'Contents' in page:
			for obj in page['Contents']:
				all_keys.append(obj['Key'])
	total_file = len(all_keys)
	print(f"目前有 {total_file} 個檔案等包裝")
	cz = 10000
	ouput_dir = "archives"
	os.makedirs(ouput_dir, exist_ok=True)
	for i in range(0, total_file, cz):
		ck = all_keys[i : i + cz]
		num = (i // cz) + 1
		true_file = f"{ouput_dir}/{month}_part_{num}.tar.gz"
		with tarfile.open(true_file, "w:gz") as b:
			print(f"正在建立{true_file}")
			count = 0
			for s in ck:
				response = s3.get_object(Bucket=bucket_name, Key=s)
				file_data = response['Body'].read()
				info = tarfile.TarInfo(name=s)
				info.size = len(file_data)
				b.addfile(tarinfo=info, fileobj=io.BytesIO(file_data))
				count = count + 1
				if count % 1000 == 0:
					print(f"已打包 {count} 個檔案")
			print(f"新檔名{true_file}壓縮完成")
	print(f"打包結束，一共 {total_file} 個檔案")
if __name__ == '__main__':
	archive()