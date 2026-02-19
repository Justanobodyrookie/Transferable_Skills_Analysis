import scrapy
import json
import os
import random
import time
import mysql.connector
from urllib.parse import urlencode
from job_crawler.items import JobCrawlerItem
from dotenv import load_dotenv
load_dotenv()

class Job_marketSpider(scrapy.Spider):
    name = "job"
    allowed_domains = ["104.com.tw"]
    start_urls = "https://www.104.com.tw/jobs/search/api/jobs"
    default_params = {
        'area': '',
        'job_cat': '',
        'jobsource': 'joblist_search',
        'order': '15',
        'page': '',
        'pagesize': '20'
    }

    db_config = {
        'host': os.getenv('MYSQL_HOST'),
        'port': os.getenv('MYSQL_PORT'),
        'user': os.getenv('MYSQL_USER'),
        'password': os.getenv('MYSQL_ROOT_PASSWORD'),
        'database': os.getenv('MYSQL_DATABASE')
    }
    def start_requests(self):
        try:
            conn = mysql.connector.connect(**self.db_config)
            cursor = conn.cursor()
            cursor.execute('select code from regions where level = 3')
            regions_code = [row[0] for row in cursor.fetchall()]
            cursor.execute('select code from job_category where level = 3')
            job_category = [row[0] for row in cursor.fetchall()]
            for r_code in regions_code:
                for j_code in job_category:
                    params = self.default_params.copy()
                    params['area'] = r_code
                    params['job_cat'] = j_code
                    params['page'] = 1
                    page = 1
                    url = f"{self.start_urls}?{urlencode(params)}"
                    yield scrapy.Request(
                            url,
                            callback=self.parse,
                            meta={
                                'reg_code': r_code,
                                'job_code': j_code,
                                'page': page
                            }
                        )
        except Exception as e:
            self.logger.info(f"資料庫連線: {e}")
        finally:
            conn.close()
            self.logger.info(f'資料庫成功關閉')
    def parse(self, response):
        reg_code = response.meta['reg_code']
        job_code = response.meta['job_code']
        page = response.meta['page']
        try:
            data = json.loads(response.text)
            jobs_list = []
            if 'data' in data and isinstance(data['data'], list):
                jobs_list = data['data']
            if not jobs_list:
                self.logger.info(f'地區分類: {reg_code}/工作分類: {job_code}, 第 {page} 頁無資料,停止')
                return
            for job in jobs_list:
                item = JobCrawlerItem()
                item['job_code'] = job['link']['job'].split('/')[-1].split('?')[0]
                item['region_code'] = job['jobAddrNo']
                item['raw_data'] = job
                raw_cat = job.get('jobCat', [])
                cate_code = json.dumps(raw_cat)
                item['category_code'] = cate_code
                yield item
            if len(jobs_list) > 0 and page < 150:
                next_page = page + 1
                params = self.default_params.copy()
                params['area'] = reg_code
                params['job_cat'] = job_code
                params['page'] = next_page
                next_url = f"{self.start_urls}?{urlencode(params)}"
                self.logger.info(f"地區代號: {reg_code}/ 工作分類: {job_code} 前往第 {page} 頁")
                yield scrapy.Request(
                    next_url,
                    callback=self.parse,
                    meta={
                        'reg_code': reg_code,
                        'job_code': job_code,
                        'page': next_page
                    }
                )
        except Exception as e:
            self.logger.info(f'爬蟲失敗: {e}')