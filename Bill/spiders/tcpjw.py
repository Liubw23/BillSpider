# -*- coding: utf-8 -*-
import time
import re
from urllib.parse import urlencode

from Bill.items import *
from Bill.util import misc
from Bill.util.misc import trace_error
from Bill.util.spider_exception import EmptyNodeException


Today = time.strftime("%Y%m%d")
Year = time.strftime("%Y")


class TcpjwSpider(scrapy.Spider):
    name = 'tcpjw'
    allowed_domains = ['tcpjw.com']
    start_urls = ['https://www.tcpjw.com/OrderList/TradingCenter']  # #pageIdx=-1
    # 配置setting
    custom_settings = {
        'DOWNLOAD_DELAY': 3,
        'LOG_LEVEL': 'DEBUG',
        'HTTPERROR_ALLOWED_CODES': [400],
        'DOWNLOADER_MIDDLEWARES': {
            'Bill.middlewares.RandomUserAgentMiddleware': 544,
            'Bill.middlewares.TcpjwMiddleware': 547,
        }
    }


    headers = {
        "content-type": "application/x-www-form-urlencoded",
        "cookie": "UserCookie=Id=10013925&UniqId=31a6f2aa-6151-4798-b0ff-deb5cd3e12a1"
                  "&Name=%e5%8c%85%e5%a4%b4%e5%b8%82%e6%b7%b1%e8%93%9d%e8%b4%b8%e6%98%93%e6%9c%89%e9%99%90%e5%85%ac%e5"
                  "%8f%b8&Phone=15902101576&Type=2",
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
        node_list = response.xpath('//*[@id="tb"]/tr')
        if not node_list:
            raise EmptyNodeException

        count = re.search(r'共 (.*?) 条记录', response.text)
        if count:
            count = count.group(1)
            size = 10
            pages = int(count) // size + 1
        else:
            pages = 1

        print('url=', response.url, ' --> 总页数：', pages)

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
            raise EmptyNodeException

        node_list = node_list[:-1]

        n = 1
        for node in node_list:
            print("种类：", str(response.meta['kind']), '*' * 10, '第' + str(response.meta['page']) + '页',  n, '*' * 10)
            n += 1
            item = BillItem()
            F2 = node.xpath('td[1]/text()').extract_first()
            if F2:
                F2 = Year + F2.replace(' ', '').replace(':', '').replace('.', '') + '00'
            else:
                F2 = ''
            item['F2'] = F2

            today = F2[:8]
            if today != Today:
                print('日期：', today, F2)
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
                F9 = Year + F9.replace('.', '/')[2:]
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
            item['FS'] = 0 if '交易完成' in FS or '竞价' in item['F12'] else 1

            item['FP'] = int(time.strftime("%Y%m%d%H%M%S"))

            item['FU'] = int(time.strftime("%Y%m%d%H%M%S"))

            print(item)
            yield item
