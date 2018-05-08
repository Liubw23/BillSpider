# -*- coding: utf-8 -*-
import os
import json
import time
import scrapy

from Bill.items import BillItem
from scrapy.conf import settings
from Bill.util.misc import trace_error


class HuipiaoxianSpider(scrapy.Spider):
    name = 'huipiaoxian'
    allowed_domains = ['huipiaoxian.com']
    start_urls = ['http://huipiaoxian.com/']

    custom_settings = {
        # 'LOG_FILE': os.path.join(settings['LOG_DIR'], name + '.txt'),
        'DOWNLOADER_MIDDLEWARES': {
            'Bill.middlewares.RandomUserAgentMiddleware': 544,
        }
    }

    # {(国股 大商 城商 三农 村镇): 银票, (其它，财务): 财票, (其它): 商票}
    kind_dict = {
        "国股": "银票",
        "城商": "银票",
        "三农": "银票",
        "村镇": "银票",
        "外资": "银票",
        "财务公司": "财票",
        "商票": "商票"
    }

    def start_requests(self):
        url = 'https://www.huipiaoxian.com:8000/v1/bills/billProduct/list?n=10&orderBy=-publishing_time&p=1'
        yield scrapy.Request(url=url, callback=self.parse, meta={'p': 1})

    @trace_error
    def parse(self, response):

        print('当前页数：', response.meta['p'])

        json_data = json.loads(response.text)
        data_list = json_data['data']['listName']

        for data in data_list:
            item = BillItem()

            item['F1'] = self.name + '+' + data['bill_number']

            F2 = data['bill_product_create_time'] / 1000
            item['F2'] = time.strftime("%Y%m%d%H%M%S", time.localtime(F2))

            item['F3'] = data['contact_name']

            item['F4'] = '出'

            item['F5'] = self.kind_dict[data['acceptor_type_name']]

            item['F6'] = data['bill_type_name']

            item['F7'] = data['acceptor_name'] + ',' + data['acceptor_type_name']

            F8 = float(data['bill_sum_price']) / 10000
            F8 = '%0.2f' % F8 + '万'
            item['F8'] = F8

            F9 = data['bill_deadline_time'] / 1000
            item['F9'] = time.strftime("%Y/%m/%d", time.localtime(F9))

            item['F10'] = str(data['day']) + '天'

            item['F11'] = ''

            item['F12'] = str(data['every_plus_amount']) + '元' if data['every_plus_amount'] else '竞价'

            item['F13'] = ''

            item['F14'] = data['contact_phone']

            # FT, FV, FP, FU, FS
            item['FS'] = 0 if data['bill_status_code'] != 801 or item['F12'] == '竞价' else 1

            item['FP'] = int(time.strftime("%Y%m%d%H%M%S"))

            item['FU'] = int(time.strftime("%Y%m%d%H%M%S"))

            print(item)
            # self.logger.info('get {item} from {url}'.format(item=item, url=response.url))
            yield item

        pages = json_data['data']['page_info']['total_page']

        for page in range(2, pages+1):
            url = 'https://www.huipiaoxian.com:8000/v1/bills/billProduct/list?n=10&orderBy=-publishing_time&p={}'\
                  .format(page)
            yield scrapy.Request(url=url, callback=self.parse, meta={'p': page})
