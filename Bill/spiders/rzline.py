# -*- coding: utf-8 -*-
import scrapy
import json
from Bill.util.send_email import EmailSender
from Bill.util import misc


class RzlineSpider(scrapy.Spider):
    name = 'rzline'
    allowed_domains = ['rzline.com']
    start_urls = ['http://www.rzline.com/web/front/quoteMarket/show']

    formdata = {
        "appVersion": "web1.1.0",
        "city": "上海市",
        "detailType": "",
        "ifDefaultCity": "true",
        "orderBy": "2",
        "page": "1",
        "quoteDate": "1524758400000",
        "quoteType": "e",
        "rows": "7"
    }

    formdata1 = {
        "appVersion": "1.3.1",
        "orgUserId": "",
        "quoteDate": "1524758400000",
        "quoteType": "e",
    }

    headers = {
        "Accept": "application/json, text/javascript, */*; q=0.01",  # 必须添加
        "Content-Type": "application/json;charset=UTF-8",            # 必须添加
        "Accept-Encoding": "gzip, deflate",
        "Accept-Language": "zh-CN,zh;q=0.9",
        "Connection": "keep-alive",
        "Host": "www.rzline.com",
        "Origin": "http://www.rzline.com",
        "X-Requested-With": "XMLHttpRequest"
    }

    def parse(self, response):
        url = 'http://www.rzline.com/web/mobuser/market/quoteShow'
        yield scrapy.Request(
                             url=url,
                             callback=self.parse_id,
                             errback=self.hand_error,
                             meta={'data': self.formdata, 'header': self.headers},
                             )

    def parse_id(self, response):
        data = response.body.decode()
        json_data = json.loads(data)
        url = 'http://www.rzline.com/web/mobuser/market/quoteDetail'
        try:
            data_list = json_data['data']
            for i in data_list:
                user_id = i['orgUserId']
                print(user_id)
                formdata1 = self.formdata1
                formdata1['orgUserId'] = str(user_id)
                yield scrapy.Request(url=url,
                                     dont_filter=True,
                                     callback=self.parse_detail,
                                     errback=self.hand_error,
                                     meta={'data': formdata1, 'header': self.headers},
                                     )

        except Exception as e:
            # 发送邮件
            title = '爬虫' + self.name + '异常'
            error_info = misc.get_error_info(str(e))
            content = '异常位置：' + error_info['pos'] + '\n' + '异常原因：' + error_info['reason']
            print('content=', content)
            EmailSender().send(title, content)
            return

    def parse_detail(self, response):
        print('parse_detail')
        print(response)
        print(response.body.decode())

    def hand_error(self, failture):
        print(failture)
