# -*- coding: utf-8 -*-
import re
import json
import time
import scrapy

from Bill.items import BillItem
from Bill.util.misc import trace_error

Today = time.strftime("%Y%m%d")
Year = time.strftime("%Y")


class PttkjSpider(scrapy.Spider):
    name = 'pttkj'
    allowed_domains = ['pttkj.net']
    start_urls = ['https://www.pttkj.net']

    custom_settings = {
        'DOWNLOADER_MIDDLEWARES': {
            'Bill.middlewares.RandomUserAgentMiddleware': 544,
            # 'Bill.middlewares.RandomProxyMiddleware': 545,
        }
    }

    base_url = 'https://www.pttkj.net/jsp/website/pjxgjson.cmdpage?method=getCpxxToIndex&opt=json&currentPage={page}'

    kind_dict = {
                 "1": ("国股", "银票"),
                 "2": ("城商", "银票"),
                 "3": ("三农", "银票"),
                 "4": ("财务公司", "财票"),
                 "5": ("其它", "商票"),
                }

    def start_requests(self):
        url = self.base_url.format(page=1)
        yield scrapy.Request(url=url,
                             callback=self.parse,
                             meta={'page': 1})

    @trace_error
    def parse(self, response):
        json_data = json.loads(response.text)
        data_list = json_data['listMap']

        if not data_list:
            return

        n = 1
        flag = 1
        for data in data_list:
            print('第{}页'.format(response.meta['page']), '*'*10, n, "*"*10)
            n += 1

            item = BillItem()

            F2 = data['ywCpxxfbsj'].replace('-', '').replace(':', '').replace(' ', '') if data['ywCpxxfbsj'] else ''
            item['F2'] = Year + F2 + '00'

            today = item['F2'][:8]
            if today != Today:
                flag = 0
                print('日期：', today)
                break

            item['F3'] = data['cprqymc'] if data['cprqymc'] else ''

            item['F4'] = '出'

            item['F5'] = self.kind_dict[data['ywCpxxCdjglx']][1] if data['ywCpxxCdjglx'] else ''

            item['F7'] = data['ywCpxxCdjg'].replace('*', '') if data['ywCpxxCdjg'] else ''

            item['F8'] = str('%.2f' % float(data['ywCpxxPjme'])) + '万' if data['ywCpxxPjme'] else ''

            item['F9'] = data['ywCpxxHpdqr'].replace('-', '/') if data['ywCpxxHpdqr'] else ''

            item['F10'] = str(data['syts']) + '天' if data['syts'] else ''

            if (item['F8'] and float(item['F8'].replace('万', '')) >= 100) \
                    or (item['F10'] and int(item['F10'].replace('天', '')) >= 190):
                item['F6'] = '电票'
            else:
                item['F6'] = ''

            item['F11'] = ''

            item['F12'] = str(data['mswkk']) + '元' if data['mswkk'] else ''

            item['F13'] = ''

            item['F14'] = None

            # FT, FV, FP, FU, FS
            item['FS'] = 0 if data['pjjyzt'] == "8" or item['F12'] == '' else 1

            item['FP'] = int(time.strftime("%Y%m%d%H%M%S"))

            item['FU'] = int(time.strftime("%Y%m%d%H%M%S"))

            url = 'https://www.pttkj.net/pjxgpage.cmdpage?method=pjdetailPage&ywCpxxNm={}'.format(data['ywCpxxNm'])
            yield scrapy.Request(url=url,
                                 priority=1,
                                 callback=self.parse_detail,
                                 meta={'item': item})

        if flag:
            page = response.meta['page'] + 1
            url = self.base_url.format(page=page)
            yield scrapy.Request(url=url,
                                 callback=self.parse,
                                 meta={'page': page})

    @trace_error
    def parse_detail(self, response):
        data = response.text
        item = response.meta['item']
        bill_no = re.search('<li>票据号码：(.*?)</li>', data)
        if bill_no:
            item['F1'] = self.name + '+' + bill_no.group(1)
        print(item)
        yield item
