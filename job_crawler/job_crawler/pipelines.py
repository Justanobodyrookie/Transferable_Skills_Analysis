# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html


# useful for handling different item types with a single interface
from itemadapter import ItemAdapter
import boto3
import os
import json
from dotenv import load_dotenv
from datetime import datetime
from botocore.exceptions import ClientError

class MinIOpipeline:
    def __init__(self):
        load_dotenv()
        endpoint = os.getenv('MINIO_ENDPOINT')
        access_key = os.getenv('MINIO_USER')
        secret_key = os.getenv('MINIO_PASSWORD')
        self.bucket_name = 'job-data'
        self.s3_client = boto3.client(
            's3',
            endpoint_url=endpoint,
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_key,
            region_name='us-east-1'
        )
    def open_spider(self, spider):
        try:
            self.s3_client.head_bucket(Bucket=self.bucket_name)
        except ClientError:
            self.s3_client.create_bucket(Bucket=self.bucket_name)
    def process_item(self, item, spider):
        try:
           code = item.get('job_code')
           reg_code = item.get('region_code')      
           date = datetime.now().strftime('%Y-%m-%d')
           s3_key = f"{date}/{reg_code}/{code}.json"
           json_file = json.dumps(dict(item), ensure_ascii=False)
           self.s3_client.put_object(
                Bucket=self.bucket_name,
                Key=s3_key,
                Body=json_file,
                ContentType='application/json'
            )
        except Exception as e:
            spider.logger.error(f"寫入MinIO出問題: {e}")
        return item
    def close_spider(self, spider):
        spider.logger.info(f"MinIO結束")