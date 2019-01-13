import scrapy
from scrapy.crawler import CrawlerProcess


class WikiCFPSpider(scrapy.Spider):
    name = 'WikiCFPSpider'
    custom_settings = {
        "LOG_ENABLED": False
    }

    def parse(self, response):
        cfp = "".join(response.xpath('.//table//div[@class="cfp"]/text()').extract())
        with open('dump.txt', 'w') as f:
            f.write(cfp)


def getCFP(url):
    process = CrawlerProcess()
    process.crawl(WikiCFPSpider, start_urls=[url])
    process.start()