import logging
from scrapy import signals
from scrapy.exceptions import NotConfigured
from job_crawler.gmail import send_error

logger = logging.getLogger(__name__)

class ErrorEmailExtension:
	@classmethod
	def from_crawler(cls, crawler):
		ext = cls()
		crawler.signals.connect(ext.spider_error, signal=signals.spider_error)
		return ext
	def spider_error(self, failure, response, spider):
		error_msg = f"Spider: {spider.name}\nURL: {response.url}\nError:\n{failure.getTraceback()}"
		logger.info(f"準備發送錯誤訊息信: {error_msg}")
		send_error(error_msg, subject=f"爬蟲錯誤: ({spider.name})")