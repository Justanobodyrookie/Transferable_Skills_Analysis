BOT_NAME = "job_crawler"

SPIDER_MODULES = ["job_crawler.spiders"]
NEWSPIDER_MODULE = "job_crawler.spiders"

# Obey robots.txt rules
ROBOTSTXT_OBEY = False
CONCURRENT_REQUESTS = 64 # 32 # 16 # 8
USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
REQUEST_FINGERPRINTER_IMPLEMENTATION = "2.7"
TWISTED_REACTOR = "twisted.internet.asyncioreactor.AsyncioSelectorReactor"
FEED_EXPORT_ENCODING = "utf-8"
DOWNLOAD_DELAY = 0.5 # 1 # 2
RANDOMIZE_DOWNLOAD_DELAY = True
COOKIES_ENABLED = True
DEFAULT_REQUEST_HEADERS = {
   "Accept": "application/json, text/javascript, */*; q=0.01",
   "Accept-Language": "zh-TW,zh;q=0.9,en-US;q=0.8,en;q=0.7",
   "Referer": "https://www.104.com.tw/jobs/search/",
   "X-Requested-With": "XMLHttpRequest",
}
ITEM_PIPELINES = {
   "job_crawler.pipelines.MinIOpipeline": 300,
}
AUTOTHROTTLE_ENABLED = True
AUTOTHROTTLE_START_DELAY = 1
AUTOTHROTTLE_MAX_DELAY = 10
AUTOTHROTTLE_TARGET_CONCURRENCY = 1.0
LOG_LEVEL = 'INFO'