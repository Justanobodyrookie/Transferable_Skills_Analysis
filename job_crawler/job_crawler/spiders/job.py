import scrapy


class Job_marketSpider(scrapy.Spider):
    name = "job"
    allowed_domains = ["104.com.tw"]
    start_urls = ["https://104.com.tw"]

    def parse(self, response):
        