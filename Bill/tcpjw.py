# -*- coding: utf-8 -*-
import scrapy
import time
from pymysql import NULL
import re

from Bill.items import *

Today = time.strftime("%Y%m%d")
Year = time.strftime("%Y")


class TcpjwSpider(scrapy.Spider):
    name = 'tcpjw'
    allowed_domains = ['tcpjw.com']
    start_urls = ['https://www.tcpjw.com/OrderList/TradingCenter?pageIdx=1']

    def start_requests(self):
        yield scrapy.Request(self.start_urls[0], meta={'page': 1})

    def parse(self, response):
        page = response.meta['page']
        print('正在爬取第{}页的数据!'.format(page))
        print(response.url)

        node_list = response.xpath('//*[@id="tb"]/tr')
        if not node_list:
            print('节点列表为空, 退出程序！')
            return

        flag = 1
        for node in node_list[:-1]:
            item = BillItem()

            F2 = node.xpath('td[1]/text()').extract_first()
            if F2:
                F2 = Year + F2.replace(' ', '').replace(':', '').replace('.', '') + '00'
            else:
                F2 = NULL
            item['F2'] = F2

            today = F2[:8]
            if today != Today:
                print('日期：', today)
                flag = 0
                break

            F4 = node.xpath('td[2]/span/text()').extract_first()
            item['F4'] = F4 if F4 else NULL

            F5 = node.xpath('td[3]/span/text()').extract_first()
            item['F5'] = F5 if F5 else NULL

            F7 = node.xpath('td[4]/text()').extract_first()
            if F7:
                F7 = F7.replace('\r\n', '').replace(' ', '')
            else:
                F7 = NULL
            item['F7'] = F7

            F8 = node.xpath('td[5]/text()').extract_first()
            if F8:
                F8 = F8.replace(' ', '')
                F8 = '%.2f' % float(F8)
                F8 = str(F8) + '万'
            else:
                F8 = NULL
            item['F8'] = F8

            F9 = node.xpath('td[6]/span/text()').extract_first()
            if F9:
                F9 = F9.replace('.', '/')
            else:
                F9 = NULL
            item['F9'] = F9

            if F9:
                start = time.mktime(time.strptime(today, '%Y%m%d'))
                end = time.mktime(time.strptime(F9.replace('/', ''), '%Y%m%d'))
                F10 = int(end - start)//(24*60*60)
                F10 = str(F10) + '天'
            else:
                F10 = NULL
            item['F10'] = F10

            if (item['F8'] and float(item['F8'].replace('万', '')) >= 100) \
                    or (item['F10'] and int(item['F10'].replace('天', '')) >= 190):
                item['F6'] = '电票'
            else:
                item['F6'] = ''

            F12 = node.xpath('td[7]/span/text()').extract_first()
            if F12:
                F12 = F12.replace('每十万扣款 ', '') + '元' if '竞价' not in F12 else F12
            else:
                F12 = NULL
            item['F12'] = F12

            item['F13'] = ''

            # FT, FV, FP, FU, FS
            FS = node.xpath('td[9]/a/text()').extract_first()
            if FS:
                FS = 1
            else:
                FS = 0
            item['FS'] = FS

            item['FP'] = int(time.strftime("%Y%m%d%H%M%S"))

            item['FU'] = int(time.strftime("%Y%m%d%H%M%S"))

            print(item)

        if flag:
            page = int(page) + 1
            url = 'https://www.tcpjw.com/OrderList/TradingCenter?pageIdx={pageNum}'\
                .format(pageNum=str(page))
            yield scrapy.Request(url,
                                 callback=self.parse,
                                 meta={'page': page})
