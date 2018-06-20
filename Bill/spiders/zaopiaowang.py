# -*- coding: utf-8 -*-
import os
import json
import time
import scrapy
from copy import deepcopy
from urllib.parse import urlencode

from Bill.util import misc
from Bill.items import BillItem
from scrapy.conf import settings
from Bill.util.misc import trace_error


Today = time.strftime("%Y%m%d")
s_values = set()


class ZaopiaowangSpider(scrapy.Spider):
    name = 'zaopiaowang'
    allowed_domains = ['zaopiaowang.com']
    start_urls = ['https://www.zaopiaowang.com/']

    custom_settings = {
        'LOG_FILE': os.path.join(settings['LOG_DIR'], name, Today + '.txt'),
        'DOWNLOADER_MIDDLEWARES': {
                                    'Bill.middlewares.RandomUserAgentMiddleware': 544,
                                    # 'Bill.middlewares.RandomProxyMiddleware': 545,
                                  }
    }

    base_url = "https://www.zaopiaowang.com/api/bill/search?"
    page_size = 100
    formdata = {
        "index": 1,
        "pageSize": page_size,
        "billType": 99,
        "bankType": 1,
        "industry": 99,
        "status": 99,
        "amount": 99,
        "days": 99,
    }

    kind_dict = {
                 1: '国股',
                 2: '城商',
                 3: '三农',
                 4: '财务公司',
                 5: '其它',
                 6: '村镇',
                 7: '外资',
                }

    def start_requests(self):
        formdata = deepcopy(self.formdata)
        for kind in self.kind_dict:
            formdata['bankType'] = kind
            url = self.base_url + urlencode(formdata)
            yield scrapy.Request(url=url,
                                 callback=self.parse,
                                 meta={'index': 1, 'bankType': kind})

    @trace_error
    def parse(self, response):
        json_data = json.loads(response.text)
        if json_data['status'] != "1":
            self.logger.debug('第{}页爬取异常, 停止爬取!'.format(response.meta['index']))
            return

        data_list = eval(json_data['data'])['list']
        data_list = sorted(data_list, key=lambda data:data['id'], reverse=True)

        n = 1
        flag = 1
        values = list()
        for data in data_list:
            print(response.meta['bankType'], '*'*10, n, "*"*10)
            self.logger.debug('正在爬取{}第{}页第{}条数据!'.format(response.meta['bankType'], response.meta['index'], n))

            n += 1

            item = BillItem()

            item['F1'] = self.name + str(data['id'])

            F2 = data['createTime'] if data['createTime'] else ''
            item['F2'] = time.strftime("%Y%m%d%H%M%S", time.localtime(F2)) if F2 else ''

            today = item['F2'][:8]
            if today != Today:
                flag = 0
                self.logger.debug('第{}页-第{}条-日期{}不为当前日期，停止爬取！'.format(response.meta['index'], n, today))
                break

            item['F3'] = None

            item['F4'] = '出'

            item['F5'] = data['billTypeName'] if data['billTypeName'] else ''

            kind = self.kind_dict[response.meta['bankType']]
            item['F7'] = data['cdCompanyName'] + ',' + kind if data['cdCompanyName'] else ''

            item['F8'] = str('%.2f' % float(data['amount'])) + '万' if data['amount'] else ''

            F9 = data['billEndTime'] if data['billEndTime'] else ''
            item['F9'] = time.strftime("%Y/%m/%d", time.localtime(F9)) if F9 else ''

            item['F10'] = str(data['days']) + '天' if data['days'] else ''

            if (item['F8'] and float(item['F8'].replace('万', '')) >= 100) \
                    or (item['F10'] and int(item['F10'].replace('天', '')) >= 190):
                item['F6'] = '电票'
            else:
                item['F6'] = ''

            item['F11'] = data['rate'] if data['rate'] else ''

            item['F12'] = str(data['amountPer10w']) + '元' if data['amountPer10w'] else ''

            item['F13'] = ''

            item['F14'] = None

            uu_str = item['F7'] + item['F8'] + item['F9'] + str(item['F11']) + item['F12']
            uu_id = misc.get_uuid(uu_str)
            item['F1'] = self.name + '+' + uu_id

            # FT, FV, FP, FU, FS
            item['FS'] = 0 if data['status'] == 9 or item['F12'] == '' else 1

            item['FP'] = int(time.strftime("%Y%m%d%H%M%S"))

            item['FU'] = int(time.strftime("%Y%m%d%H%M%S"))

            if item['F1'] not in s_values:
                s_values.add(item['F1'])
                values.append(item)

        for item in values:
            if item['F1'] in s_values:
                yield item

        if flag:
            formdata = deepcopy(self.formdata)
            index = response.meta['index'] + 1
            formdata['index'] = index
            formdata['bankType'] = response.meta['bankType']
            url = self.base_url + urlencode(formdata)
            yield scrapy.Request(url=url,
                                 callback=self.parse,
                                 meta={'index': index, 'bankType': response.meta['bankType']})
