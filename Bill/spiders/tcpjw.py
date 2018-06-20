# -*- coding: utf-8 -*-
import re
import os
import time
from urllib.parse import urlencode
from scrapy.exceptions import CloseSpider

from Bill.items import *
from Bill.util import misc
from scrapy.conf import settings
from Bill.util.misc import trace_error
from Bill.util.spider_exception import EmptyNodeException
from Bill.request_spider.tcpjw_login import get_cookie,set_cookie


Today = time.strftime("%Y%m%d")
Year = time.strftime("%Y")
s_values = set()


class TcpjwSpider(scrapy.Spider):
    name = 'tcpjw'
    allowed_domains = ['tcpjw.com']
    start_urls = ['https://www.tcpjw.com/OrderList/TradingCenter']  # #pageIdx=-1
    # 配置setting
    custom_settings = {
        'DOWNLOAD_DELAY': 3,
        'LOG_LEVEL': 'DEBUG',
        'LOG_FILE': os.path.join(settings['LOG_DIR'], name, Today + '.txt'),
        'HTTPERROR_ALLOWED_CODES': [400],
        'DOWNLOADER_MIDDLEWARES': {
            'Bill.middlewares.RandomUserAgentMiddleware': 544,
            'Bill.middlewares.TcpjwMiddleware': 547,
        }
    }

    headers = {
        "content-type": "application/x-www-form-urlencoded",
        "cookie": get_cookie(),
    }

    # {(国股 大商 城商 三农 村镇):银票, (其它，财务):财票, (其它):商票}
    kind_dict = {
                 "1": ("国股", "银票"),
                 "2": ("城商", "银票"),
                 "3": ("三农", "银票"),
                 "4": ("财务公司", "财票"),
                 "6": ("村镇", "银票"),
                 "7": ("外资", "银票"),
                 "8": ("商票", "商票"),
                 }

    def start_requests(self):
        for kind in self.kind_dict:
            formdata = {"pageIdx": "1", "pt_bid": kind}
            url = self.start_urls[0] + "?" + urlencode(formdata)
            yield scrapy.Request(url=url,
                                 callback=self.parse,
                                 meta={'page': 1,
                                       'kind': kind,
                                       'header': self.headers,
                                       'data': formdata})

    @trace_error
    def parse(self, response):
        print('response is ', response.status)
        node_list = response.xpath('//*[@id="tb"]/tr')
        if not node_list:
            self.logger.debug(' 节点列表1为空')
            set_cookie()
            raise EmptyNodeException('节点列表1为空')

        count = re.search(r'共 (.*?) 条记录', response.text)
        if count:
            count = count.group(1)
            self.logger.debug('共{}条数据'.format(count))
            size = 10
            pages = int(count) // size + 1
        else:
            pages = 1

        self.logger.debug('类型{}总页数{}'.format(response.meta['kind'], pages))

        for page in range(1, pages+1):
            formdata = {"pageIdx": "{}".format(page), "pt_bid": response.meta['kind']}
            url = self.start_urls[0] + "?" + urlencode(formdata)
            if_filter = True if page == 1 else False
            yield scrapy.Request(url=url,
                                 priority=1,
                                 dont_filter=if_filter,
                                 callback=self.parse_detail,
                                 meta={'page': page,
                                       'kind': response.meta['kind'],
                                       'header': self.headers,
                                       'data': formdata})

    @trace_error
    def parse_detail(self, response):
        node_list = response.xpath('//*[@id="tb"]/tr')
        if not node_list:
            self.logger.debug(' 节点列表2为空')
            set_cookie()
            self.headers["cookie"] = get_cookie()
            raise EmptyNodeException('节点列表2为空')

        node_list = node_list[:-1]

        n = 1
        for node in node_list:
            self.logger.debug('{}第{}页第{}条'.format(response.meta['kind'], response.meta['page'], n))
            n += 1
            item = BillItem()
            F2 = node.xpath('td[1]/text()').extract_first()
            item['F2'] = Year + F2.replace(' ', '').replace(':', '').replace('.', '') + '00' if F2 else ''

            today = item['F2'][:8]
            if today != Today:
                self.logger.debug('{}第{}页-第{}条-日期{}不为当前日期，停止爬取！'
                                  .format(response.meta['kind'], response.meta['page'], n, today))
                break

            item['F3'] = None

            item['F4'] = '出'

            kind = response.meta['kind']
            F5 = self.kind_dict[kind][1]
            item['F5'] = F5

            F7 = node.xpath('td[2]/span/text()').extract_first()
            if F7:
                F7 = F7.replace('\r\n', '').replace(' ', '')
            else:
                F7 = None
            item['F7'] = F7 + ',' + self.kind_dict[kind][0]

            F8 = node.xpath('td[3]/text()').extract_first()
            if F8:
                F8 = F8.replace(' ', '')
                F8 = '%.2f' % float(F8)
                F8 = str(F8) + '万'
            else:
                F8 = None
            item['F8'] = F8

            F9 = node.xpath('td[4]/text()').extract_first()
            if F9:
                F9 = F9.replace('\r\n', '').replace('\t', '').replace(' ', '')
                F10 = F9.split('(剩')[1][:-1] + '天'
                F9 = F9.split('(剩')[0]
                F9 = '20' + F9.replace('.', '/')
            else:
                F9 = None
                F10 = None
            item['F9'] = F9

            item['F10'] = F10

            if (item['F8'] and float(item['F8'].replace('万', '')) >= 100) \
                    or (item['F10'] and int(item['F10'].replace('天', '')) >= 190):
                item['F6'] = '电票'
            else:
                item['F6'] = ''

            item['F11'] = None

            F12 = node.xpath('td[5]/span/text()').extract_first()
            if F12:
                F12 = F12.replace('\r\n', '').replace('\t', '').replace(' ', '')
                F12 = F12.replace('每十万扣款 ', '') + '元' if '竞价' not in F12 else F12
            else:
                F12 = None
            item['F12'] = F12

            item['F13'] = ''
            item['F14'] = None

            uu_str = item['F7'] + item['F8'] + item['F9'] + item['F12']
            uu_id = misc.get_uuid(uu_str)
            item['F1'] = self.name + '+' + str(uu_id)

            # FT, FV, FP, FU, FS
            FS = ''.join(node.xpath('td[7]').extract()).replace('\r\n', '').replace(' ', '')
            item['FS'] = 0 \
                if '交易完成' in FS \
                   or '竞价' in item['F12'] \
                   or '-' in item['F10'] \
                   or int(item['F10'][:-1]) <= 0 \
                else 1

            item['FP'] = int(time.strftime("%Y%m%d%H%M%S"))

            item['FU'] = int(time.strftime("%Y%m%d%H%M%S"))

            if item['F1'] not in s_values:
                s_values.add(item['F1'])
                print(item)
                yield item
            else:
                self.logger.debug('该票据重复: {}'.format(item['F7']))
                print('该票据{}重复'.format(item['F7']))
