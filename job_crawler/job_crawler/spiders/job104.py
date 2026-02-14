import scrapy


class Job104Spider(scrapy.Spider):
    name = "job104"
    allowed_domains = ["104.com.tw"]
    start_urls = ["https://104.com.tw"]

    def parse(self, response):
        