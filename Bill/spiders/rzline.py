# -*- coding: utf-8 -*-
import scrapy
import json
import time
import copy

from Bill.items import BillItem, RzlineItem
from Bill.util import misc
from Bill.util.send_email import EmailSender

Today = time.strftime("%Y%m%d")


class RzlineSpider(scrapy.Spider):
    name = 'rzline'
    allowed_domains = ['rzline.com']
    start_urls = ['http://www.rzline.com/web/front/quoteMarket/show']

    custom_settings = {
        "LOG_LEVEL": "INFO"
    }

    # 查询日期
    quoteDate = time.mktime(time.strptime(Today, '%Y%m%d'))
    quoteDate = str(quoteDate).replace('.', '') + '00'

    quoteType_list = ['s', 'se', 'b']
    kind_dict = {'gg': '国股', 'sh': '城商', 'sn': '三农',
                 'busEle': '电子', 'busPaper': '纸质',
                 'gq': '国企', 'yq': '央企'}
    busType_dict = {"1": "买断", "2": "直贴", "0": ""}

    # 查询条数
    rows = 100

    formdata = {
        "appVersion": "iOS2.6.1",
        "city": "全国",
        "detailType": "",
        "ifDefaultCity": "false",
        "orderBy": "2",
        "page": 1,
        "quoteDate": quoteDate,
        "rows": rows,
    }

    formdata1 = {
        "appVersion": "2.6.1",
        "orgUserId": "",
        "quoteDate": quoteDate,
        "quoteType": "e",
    }

    headers = {
        "Accept": "application/json, text/javascript, */*; q=0.01",  # 必须添加
        "Content-Type": "application/json;charset=UTF-8",            # 必须添加
        "Accept-Encoding": "gzip, deflate",
        "Accept-Language": "zh-CN,zh;q=0.9",
        "Connection": "keep-alive",
        "Content-Length": "82",
        "Host": "www.rzline.com",
        "Origin": "http://www.rzline.com",
        "Referer": "http://www.rzline.com/web/front/quoteMarket/show",
        "X-Requested-With": "XMLHttpRequest"
    }

    def parse(self, response):
        base_url = 'http://www.rzline.com/web/mobuser/market/quoteShow'
        formdata = copy.deepcopy(self.formdata)
        url = base_url + '&page=' + str(formdata['page'])
        yield scrapy.Request(
                             url=url,
                             callback=self.parse_id,
                             errback=self.hand_error,
                             meta={'data': formdata, 'header': self.headers},
                             )

    def parse_id(self, response):
        data = response.body.decode()
        json_data = json.loads(data)
        id_url = 'http://www.rzline.com/web/mobuser/market/quoteDetail'
        flag = 1
        try:
            data_list = json_data['data']
            if data_list:
                for i in data_list:
                    user_id = i['orgUserId']
                    formdata1 = copy.deepcopy(self.formdata1)
                    formdata1['orgUserId'] = str(user_id)
                    url = id_url + '&orgUserId=' + str(user_id) + '&quoteType=' + formdata1['quoteType']
                    quoteType_list = copy.deepcopy(self.quoteType_list)
                    yield scrapy.Request(url=url,
                                         priority=1,
                                         callback=self.parse_detail,
                                         errback=self.hand_error,
                                         meta={'data': formdata1,
                                               'header': self.headers,
                                               'user_id': user_id,
                                               'quoteType': formdata1['quoteType'],
                                               'quoteType_list': quoteType_list}
                                         )
            else:
                flag = 0

        except Exception as e:
            # 发送邮件
            title = '爬虫' + self.name + '异常'
            error_info = misc.get_error_info(str(e))
            content = '异常位置：' + error_info['pos'] + '\n' + '异常原因：' + error_info['reason']
            EmailSender().send(title, content)
            return

        # 下一页
        if flag:
            print('当前页数：', response.meta['data']['page'])
            formdata = response.meta['data']
            formdata['page'] += 1
            base_url = 'http://www.rzline.com/web/mobuser/market/quoteShow'
            url = base_url + '&page=' + str(formdata['page'])
            yield scrapy.Request(
                                 url=url,
                                 callback=self.parse_id,
                                 errback=self.hand_error,
                                 meta={'data': formdata,
                                       'header': self.headers},
                                )

    def parse_detail(self, response):
        res = response.body.decode()
        data = json.loads(res)
        data = data['data']

        price_list = data['quotePriceDetailList']

        if not price_list:
            formdata1 = response.meta['data']
            quoteType_list = response.meta['quoteType_list']
            if quoteType_list:
                quoteType = quoteType_list.pop()
                formdata1['quoteType'] = quoteType
                id_url = 'http://www.rzline.com/web/mobuser/market/quoteDetail'
                url = id_url + '&orgUserId=' + str(response.meta['user_id']) + '&quoteType=' + quoteType
                yield scrapy.Request(url=url,
                                     priority=1,
                                     callback=self.parse_detail,
                                     errback=self.hand_error,
                                     meta={'data': formdata1,
                                           'header': self.headers,
                                           'user_id': response.meta['user_id'],
                                           'quoteType': quoteType,
                                           'quoteType_list': quoteType_list},
                                     )

        else:

            for price in price_list:
                item = RzlineItem()
                try:
                    # 发布时间
                    F2 = price['createTime'] if price['createTime'] else None
                    if F2:
                        F2 = F2.replace('-', '').replace(':', '').replace(' ', '')
                    else:
                        F2 = None
                    item['F2'] = F2

                    # 机构
                    detail_type = price['detailType'] if price['detailType'] else ''
                    if detail_type:
                        kind = self.kind_dict[detail_type]
                    else:
                        kind = ''
                    F3 = data['orgInfoDto']['orgWholename'] if data['orgInfoDto'] else ''
                    item['F3'] = F3 + ',' + kind if F3 else ''

                    # 金额
                    item['F4'] = price['price'] if price['price'] else ''

                    # 类型
                    item['F5'] = kind

                    # 每十万
                    F6 = price['tenInterest'].replace('--', '') if price['tenInterest'] else ''
                    item['F6'] = F6 + '元' if F6 else ''

                    # 期限
                    F7 = price['quoteDays'] if price['quoteDays'] else ''
                    item['F7'] = F7

                    # 额度
                    item['F8'] = price['quoteAmount']

                    # 业务类型
                    item['F9'] = self.busType_dict[data['busType']] if data['busType'] else ''

                    # 联系人
                    F10 = data['accountManagerList'][0]['name'] if data['accountManagerList'] else ''
                    item['F10'] = F10

                    # 联系方式
                    F11 = data['accountManagerList'][0]['mobPhone'] if data['accountManagerList'] else ''
                    item['F11'] = F11

                    # 唯一标识
                    uu_str = item['F3'] + str(item['F4']) + item['F6'] + item['F7'] + str(item['F8']) + item['F9']
                    uu_id = misc.get_uuid(uu_str)
                    item['F1'] = uu_id

                    # FT, FV, FP, FU, FS
                    FS = data['ifStartTrad'] if data['ifStartTrad'] else None
                    item['FS'] = 0 if FS != "1" else 1

                    item['FP'] = int(time.strftime("%Y%m%d%H%M%S"))

                    item['FU'] = int(time.strftime("%Y%m%d%H%M%S"))

                    yield item

                except Exception as e:
                    title = '爬虫' + self.name + '异常'
                    error_info = misc.get_error_info(str(e))
                    content = '异常位置：' + error_info['pos'] + '\n' + '异常原因：' + error_info['reason']
                    EmailSender().send(title, content)
                    raise Exception

    def hand_error(self, failture):
        print(failture)
