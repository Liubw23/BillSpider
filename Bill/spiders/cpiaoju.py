# -*- coding: utf-8 -*-
import re
import os
import time
import scrapy

from Bill.items import BillItem
from scrapy.conf import settings
from Bill.util.misc import trace_error

Today = time.strftime("%Y%m%d")


class CpiaojuSpider(scrapy.Spider):
    name = 'cpiaoju'
    allowed_domains = ['cpiaoju.com']
    start_urls = ['http://www.cpiaoju.com/Draft']

    custom_settings = {
        'LOG_FILE': os.path.join(settings['LOG_DIR'], name, Today + '.txt'),
        'DOWNLOADER_MIDDLEWARES': {
                                    'Bill.middlewares.RandomUserAgentMiddleware': 544,
                                    # 'Bill.middlewares.RandomProxyMiddleware': 545,
                                  }
    }

    flag = 1

    kind_dict = {
        '纸银': ('', '银票'),
        '电银': ('电票', '银票'),
        '纸商': ('', '商票'),
        '电商': ('电票', '商票'),
    }

    def start_requests(self):
        yield scrapy.Request(url=self.start_urls[0], meta={'page': 1})

    @trace_error
    def parse(self, response):
        self.logger.debug('当前页数：{}'.format(response.meta['page']))
        node_list = response.xpath('//ul[@class="R_ullist1 clearfix"]')

        for node in node_list:
            url = node.xpath('li[1]/a/@href').extract_first()
            full_url = 'http://www.cpiaoju.com' + url
            if self.flag:
                yield scrapy.Request(url=full_url, callback=self.parse_detail, priority=1)
            else:
                break
        else:
            page = response.meta['page'] + 1
            next_url = 'http://www.cpiaoju.com/Draft?&page={}'.format(page)
            yield scrapy.Request(url=next_url, meta={'page': page}, callback=self.parse)

    @trace_error
    def parse_detail(self, response):
        item = BillItem()

        item['F1'] = self.name + '+' + response.url.split('detail/')[1].replace('.html', '')

        F2 = response.xpath('//div[@class="R_seulp1 R_fontSize3 R_marginBot"]/span[3]/text()').extract_first()
        F2 = F2.replace('发布日期：', '').replace('-', '').replace(' ', '')
        item['F2'] = F2 + '000000'

        item['F3'] = None

        item['F4'] = '出'

        kind = response.xpath('//dt[contains(text(), "票据类型")]/../dd/text()').extract_first()
        item['F5'] = self.kind_dict[kind][1]

        item['F6'] = self.kind_dict[kind][0]

        F7_1 = response.xpath('//div[@class="R_seulp1 R_fontSize3 R_marginBot"]/span[2]/text()').extract_first()
        F7_2 = response.xpath('//dt[contains(text(), "承兑银行类型")]/../dd/text()').extract_first()
        F7_2 = F7_2 if F7_2 else ''
        item['F7'] = F7_1 + ',' + F7_2 if F7_1 else ''

        F8 = response.xpath('//dt[contains(text(), "票据金额")]/../dd/text()').extract_first()
        F8 = '%.2f' % float(F8.replace('万元', ''))
        item['F8'] = F8 + '万'

        F9 = response.xpath('//dt[contains(text(), "汇票到期日")]/../dd/text()').extract_first()
        F9 = F9.replace('-', '/') if F9 else ''
        item['F9'] = F9

        F10 = response.xpath('//dt[contains(text(), "剩余天数")]/../dd/text()').extract_first()
        F10 = F10.replace(' ', '').replace('\r\n', '') if F10 else ''
        item['F10'] = F10

        F11 = response.xpath('//dt[contains(text(), "期望利率")]/../dd/span/text()').extract_first()
        F11 = F11.replace('\r\n', '').replace(' ', '').replace('%', '').replace('暂无', '') if F11 else ''
        item['F11'] = F11

        item['F12'] = None

        item['F13'] = ''

        item['F14'] = None

        # FT, FV, FP, FU, FS
        FS = re.search(r'进行中', response.text)
        item['FS'] = 1 if FS and F11 else 0

        item['FP'] = int(time.strftime("%Y%m%d%H%M%S"))

        item['FU'] = int(time.strftime("%Y%m%d%H%M%S"))

        print(item)

        if F2 != Today:
            self.flag = 0
        else:
            pass
            yield item