# -*- coding: utf-8 -*-
import json
import time
import scrapy
from copy import deepcopy
from urllib.parse import urlencode

from Bill.items import BillItem

Today = time.strftime("%Y%m%d")


class ZaopiaowangSpider(scrapy.Spider):
    name = 'zaopiaowang'
    allowed_domains = ['zaopiaowang.com']
    start_urls = ['https://www.zaopiaowang.com/']

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

    def parse(self, response):
        json_data = json.loads(response.text)

        if json_data['status'] != "1":
            return

        data_list = eval(json_data['data'])['list']
        data_list = sorted(data_list, key=lambda data:data['id'], reverse=True)

        n = 1
        flag = 1
        for data in data_list:
            print(response.meta['bankType'], '*'*10, n, "*"*10)
            n += 1

            item = BillItem()

            item['F1'] = self.name + str(data['id'])

            F2 = data['createTime'] if data['createTime'] else ''
            item['F2'] = time.strftime("%Y%m%d%H%M%S", time.localtime(F2)) if F2 else ''

            today = item['F2'][:8]
            if today != Today:
                flag = 0
                break

            item['F3'] = None

            item['F4'] = '出'

            item['F5'] = data['billTypeName'] if data['billTypeName'] else ''

            kind = self.kind_dict[response.meta['bankType']]
            item['F7'] = data['cdCompanyName'] + ',' + kind if data['cdCompanyName'] else ''

            item['F8'] = str(data['amount']) + '万' if data['amount'] else ''

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

            # FT, FV, FP, FU, FS
            item['FS'] = 0 if data['status'] == 9 else 1

            item['FP'] = int(time.strftime("%Y%m%d%H%M%S"))

            item['FU'] = int(time.strftime("%Y%m%d%H%M%S"))

            print(item)
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
