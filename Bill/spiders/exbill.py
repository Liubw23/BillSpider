# -*- coding: utf-8 -*-
import scrapy
import re
import time
import json
import requests

from Bill.items import *
from Bill.util import misc
from Bill.util.send_email import EmailSender
from Bill.util.spider_exception import EmptyNodeException

Today = time.strftime("%Y-%m-%d")


class ExbillSpider(scrapy.Spider):
    name = 'exbill'
    allowed_domains = ['exbill.cn']
    start_urls = ['https://www.exbill.cn/login/userLogin.json']

    custom_settings = {
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
        print('当前用户：', user)
        url = 'https://www.exbill.cn/purchase/purchaseList.vjson?' \
              'keyWord=&pageNum=1&purchaseType1=1'

        yield scrapy.Request(url, callback=self.parse_detail, cookies=cookies)

    def parse_detail(self, response):
        page = re.search(r'pageNum=(\d+)&', response.url).group(1)
        print('{}正在爬取第{}页的数据!'.format(self.name, page))

        node_list = response.xpath('/html/body/div/ul/li')

        if not node_list:
            print('节点列表为空, 退出程序！')
            try:
                raise EmptyNodeException
            except EmptyNodeException as e:
                title = '爬虫' + self.name + '异常'
                error_info = misc.get_error_info(str(e))
                content = '异常位置：' + error_info['pos'] + '\n' + '异常原因：' + error_info['reason']
                EmailSender().send(title, content)
                return

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

            print('*' * 10, n, '*' * 10)
            n += 1

            raw_data = node.extract()
            data = ''.join(node.xpath('.//text()').extract()).replace('\r\n', '').replace(' ', '')

            today = re_today.search(data).group()
            if today != Today:
                print('日期：', today)
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

            try:
                F7 = data.split('***')[0] + ',' + data.split('***')[1][:2]
            except IndexError:
                F7 = None
            item['F7'] = F7

            try:
                F5 = data.split('***')[1][:2]
                if F5 in ['国股', '大商', '城商', '三农', '村镇']:
                    F5 = '银票'
                elif F5 == '其它' and '财务' in F7:
                    F5 = '财票'
                else:
                    F5 = '商票'
            except IndexError:
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

            print(item)
            values.append(item)

        for item in values:
            url = 'https://www.exbill.cn/user/getUserInfo.json?userNo={}'.format(item['F3'])
            yield scrapy.Request(url,
                                 callback=self.parse_other,
                                 meta={'item': item},
                                 priority=1,
                                 dont_filter=True)
        else:
            page = int(page) + 1

            if flag == 1:
                url = 'https://www.exbill.cn/purchase/purchaseList.vjson?' \
                      'keyWord=&pageNum={pageNum}&purchaseType1=1'.format(pageNum=str(page))
                yield scrapy.Request(url, callback=self.parse_detail)

    def parse_other(self, response):
        item = response.meta['item']
        data = json.loads(response.text)
        try:
            item['F3'] = data['result']['userInfo']['name']
            item['F14'] = data['result']['userInfo']['mobile']
        except Exception as e:
            item['F3'] = None
            item['F14'] = None
            title = '爬虫' + self.name + '异常'
            error_info = misc.get_error_info(str(e))
            content = '异常位置：' + error_info['pos'] + '\n' + '异常原因：' + error_info['reason']
            EmailSender().send(title, content)
            return

        yield item




