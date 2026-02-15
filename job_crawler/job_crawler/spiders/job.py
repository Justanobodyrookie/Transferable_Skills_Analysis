import scrapy
import json
import mysql.connector
from dotenv import load_dotenv
load_dotenv()

class Job_marketSpider(scrapy.Spider):
    name = "job"
    allowed_domains = ["104.com.tw"]
    start_urls = [f"https://www.104.com.tw/jobs/search/?jobsource=joblist_search&mode=s&order=16&page=1&area={}&jobcat={}"]
    def parse(self):
        