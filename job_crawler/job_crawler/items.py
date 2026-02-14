# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

import scrapy


class JobCrawlerItem(scrapy.Item):
    # name = scrapy.Field()
    
    # jobs
    # 104的工作代號
    job_code = scrapy.Field()
    # 職位名稱
    job_title = scrapy.Field()
    # 縣市
    cnc = scrapy.Field()
    # 地點
    location = scrapy.Field()
    # 歡迎各類人
    special = scrapy.Field()
    # --條件要求
    # 工作經驗
    work_exper = scrapy.Field()
    # 學歷要求
    educational = scrapy.Field()
    # 科系要求
    d_requirements = scrapy.Field()
    # 語文條件
    language = scrapy.Field()
    # 工作技能
    workskill = scrapy.Field()
    # 其他條件
    other = scrapy.Field()
    # 薪水區間
    salary_min = scrapy.Field()
    salary_max = scrapy.Field()
    # 面議
    negotiable = scrapy.Field()
    # 職位連結
    link = scrapy.Field()
    
    # company
    # 公司
    company = scrapy.Field()
    
    # job_stats
    # 更新時間
    update_date = scrapy.Field()
    # 應徵人數
    apply_num = scrapy.Field()
    
    # skill
    # 技能
    skills = scrapy.Field()
    # 擅長工具 good at tools
    gat = scrapy.Field()
    
    # rules
    # 出差
    obt = scrapy.Field()
    # 上班時段
    job_time = scrapy.Field()
    # 休假制度
    vaction = scrapy.Field()
    
    # welfare
    # --待遇
    # 福利
    bonn = scrapy.Field()
    # 福利自介(會從裡面萃取精華出來)
    bonn_text = scrapy.Field()