# -*- coding: utf-8 -*-
import scrapy
import re
import os
import time
import json
import requests
from scrapy.exceptions import CloseSpider

from Bill.items import *
from Bill.util import misc
from scrapy.conf import settings
from Bill.util.send_email import EmailSender
from Bill.util.spider_exception import EmptyNodeException

Today = time.strftime("%Y-%m-%d")
s_values = set()
user_no_dict = dict()


class ExbillSpider(scrapy.Spider):
    name = 'exbill'
    allowed_domains = ['exbill.cn']
    start_urls = ['https://www.exbill.cn/login/userLogin.json']

    custom_settings = {
        'LOG_FILE': os.path.join(settings['LOG_DIR'], name, Today.replace('-', '') + '.txt'),
        'DOWNLOADER_MIDDLEWARES': {
                                    'Bill.middlewares.RandomUserAgentMiddleware': 544,
                                    # 'Bill.middlewares.RandomProxyMiddleware': 545,
                                  }
    }

    formdata = {
        'loginname': '15902101576',
        'pwd': 'cHIxMjM0NTY='
        # 'piccode': '',
        # 'uuid': '95c87c42c8f341a7bb78bd11ad38264f'
    }

    def start_requests(self):

        data = requests.post(url=self.start_urls[0],
                             data=self.formdata,
                             verify=False)
        cookie = requests.utils.dict_from_cookiejar(data.cookies)

        yield scrapy.Request(url='https://www.exbill.cn/index.htm',
                             cookies=cookie,
                             callback=self.parse,
                             meta={'cookie': cookie})

    def parse(self, response):

        cookies = {"nickName": "",
                   "avatar": "undefined",
                   "Hm_lvt_276269ff0ec9b043e424366cfa45ae18": "1524193588",
                   "uid": "009un0000003693accid",
                   "sdktoken": "1bc71cb8e44554d9f4a941777156abfc",
                   "Hm_lpvt_276269ff0ec9b043e424366cfa45ae18": "1524194209"}
        cookies.update(response.meta['cookie'])

        user = response.xpath('/html/body/div[1]/div[2]/div/div/a[1]/em[2]/text()').extract_first()
        self.logger.debug('当前用户：'.format(user))

        url = 'https://www.exbill.cn/purchase/purchaseList.vjson?' \
              'keyWord=&pageNum=1&purchaseType1=1'

        yield scrapy.Request(url, callback=self.parse_detail, cookies=cookies)

    def parse_detail(self, response):
        page = re.search(r'pageNum=(\d+)&', response.url).group(1)
        self.logger.debug('{}正在爬取第{}页的数据!'.format(self.name, page))

        node_list = response.xpath('/html/body/div/ul/li')

        if not node_list:
            self.logger.debug('节点列表为空, 退出程序！')
            try:
                raise EmptyNodeException
            except EmptyNodeException as e:
                title = '爬虫' + self.name + '异常'
                error_info = misc.get_error_info(str(e))
                content = '异常位置：' + error_info['pos'] + '\n' + '异常原因：' + error_info['reason']
                EmailSender().send(title, content)
                raise CloseSpider

        # 正则

        re_today = re.compile(r'\d{4}-\d{2}-\d{2}')
        re_FS = re.compile(r'已成交')

        re_F1 = re.compile(r'(SV\d+).htm')
        re_F2 = re.compile(r'(\d{4}-\d{2}-\d{2}.*?)查看详情')
        re_F3 = re.compile(r'this,\'(.*?)accid\'')
        re_F8 = re.compile(r'\d{0,2},{0,1}\d+\.\d+万')
        re_F9 = re.compile(r'\d{4}/\d{2}/\d{2}')
        re_F10 = re.compile(r'\d+天')
        re_F11 = re.compile(r'\d+\.\d+%')
        re_F12 = re.compile(r'\d+\.\d+元|\d+元')

        flag = 1
        n = 1
        values = []
        for node in node_list:

            item = BillItem()
            self.logger.debug('正在爬取第{}页第{}条数据'.format(page, n))
            n += 1

            raw_data = node.extract()
            data = ''.join(node.xpath('.//text()').extract()).replace('\r\n', '').replace(' ', '')

            today = re_today.search(data).group()
            if today != Today:
                print('日期：', today)
                self.logger.debug('第{}页-第{}条-日期{}不为当前日期，停止爬取！'.format(page, n, today))
                flag = 0
                break

            # F1-F13(F3-联系人,F14-联系方式)
            F1 = re_F1.search(raw_data)
            item['F1'] = F1.group(1) if F1 else None

            F2 = re_F2.search(data)
            F2 = F2.group(1).replace('-', '').replace(':', '') if F2 else None
            item['F2'] = F2

            F3 = re_F3.search(raw_data)
            F3 = F3.group(1).replace('un', 'UN') if F3 else None
            item['F3'] = F3

            item['F4'] = '出'

            F5 = response.xpath('//span[@class="tips"]/text()').extract_first()
            F5 = F5 if F5 else ''
            F7 = response.xpath('//span[@class="corname"]/@title').extract_first()
            F7 = F7.replace('*', '') if F7 else ''
            item['F7'] = F7 + ',' + F5

            try:
                if F5 in ['国股', '大商', '城商', '三农', '村镇']:
                    F5 = '银票'
                elif F5 == '其它' and '财务' in F7:
                    F5 = '财票'
                else:
                    F5 = '商票'
            except:
                F5 = None
            item['F5'] = F5

            F8 = re_F8.search(data)
            if F8:
                F8 = F8.group().replace(',', '').replace('万', '')
                F8 = '%.2f' % float(F8)
                F8 = str(F8) + '万'
            else:
                F8 = None
            item['F8'] = F8

            F9 = re_F9.search(data)
            item['F9'] = F9.group() if F9 else None

            F10 = re_F10.search(data)
            item['F10'] = F10.group() if F10 else None

            if (item['F8'] and float(item['F8'].replace('万', '')) >= 100) \
                    or (item['F10'] and int(item['F10'].replace('天', '')) >= 190):
                item['F6'] = '电票'
            else:
                item['F6'] = ''

            F11 = re_F11.search(data)
            item['F11'] = F11.group().replace('%', '') if F11 else None

            F12 = re_F12.search(data)
            item['F12'] = F12.group() if F12 else None

            item['F13'] = ''

            # FT, FV, FP, FU, FS
            FS = re_FS.search(raw_data)
            item['FS'] = 0 if FS else 1

            item['FP'] = int(time.strftime("%Y%m%d%H%M%S"))

            item['FU'] = int(time.strftime("%Y%m%d%H%M%S"))

            if item['F1'] not in s_values:
                s_values.add(item['F1'])
                values.append(item)
            else:
                self.logger.debug('该票据重复: {}'.format(item['F1'] + item['F7']))
                print('该票据{}重复'.format(item['F1'] + item['F7']))

        for item in values:
            detail_url = 'https://www.exbill.cn/purchase/records/{}.htm'.format(item['F1'])
            yield scrapy.Request(detail_url, self.parse_name, meta={'item': item})


        else:
            page = int(page) + 1

            if flag == 1:
                url = 'https://www.exbill.cn/purchase/purchaseList.vjson?' \
                      'keyWord=&pageNum={pageNum}&purchaseType1=1'.format(pageNum=str(page))
                yield scrapy.Request(url, callback=self.parse_detail)

    def parse_name(self, response):
        item = response.meta['item']
        name = response.xpath('//div[@class="bill-base-bank"]/text()').extract_first()
        name = name.split('*')[0]
        name = name.replace(' ', '').replace('小回头', '').replace('大回头', '')
        kind = item['F7'].split(',')[1]
        item['F7'] = ','.join((name, kind))

        url = 'https://www.exbill.cn/user/getUserInfo.json?userNo={}'.format(item['F3'])
        if item['F3'] in user_no_dict:
            user_no = item['F3']
            item['F3'] = user_no_dict[user_no][0]
            item['F14'] = user_no_dict[user_no][1]
            yield item
            print(item)
        else:
            yield scrapy.Request(url,
                                 callback=self.parse_other,
                                 meta={'item': item},
                                 priority=1,
                                 dont_filter=True)

    def parse_other(self, response):
        item = response.meta['item']
        data = json.loads(response.text)
        user_no = item['F3']

        try:
            item['F3'] = data['result']['userInfo']['name']
            item['F14'] = data['result']['userInfo']['mobile']
            user_no_dict[user_no] = (item['F3'], item['F14'])
            yield item
            print(item)
        except Exception as e:
            item['F3'] = None
            item['F14'] = None
            title = '爬虫' + self.name + '异常'
            error_info = misc.get_error_info(str(e))
            content = '异常位置：' + error_info['pos'] + '\n' + '异常原因：' + error_info['reason']
            EmailSender().send(title, content)
            raise CloseSpider
