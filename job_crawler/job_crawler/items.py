# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

import scrapy


class JobCrawlerItem(scrapy.Item):
    # name = scrapy.Field()

    job_code = scrapy.Field()
    raw_data = scrapy.Field()
    category_code = scrapy.Field()
    region_code = scrapy.Field()
    
    # company_name = scrapy.Field()

    # job_code = scrapy.Field()
    # snapshot_date = scrapy.Field()
    # job_title = scrapy.Field()
    # location = scrapy.Field()
    # apply_num = scrapy.Field()
    # salary = scrapy.Field()
    # negotiable = scrapy.Field()
    # yearbonus = scrapy.Field()
    # job_released = scrapy.Field()
    # obt = scrapy.Field()
    # no_exper = scrapy.Field()
    # remote = scrapy.Field()

    # job_time = scrapy.Field()
    # vacation = scrapy.Field()
    # link = scrapy.Field()
    # skill_list = scrapy.Field()
    # benefit_list = scrapy.Field()
    # special = scrapy.Field()