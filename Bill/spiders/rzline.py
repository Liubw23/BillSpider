# -*- coding: utf-8 -*-
import os
import json
import time
import copy
import scrapy
import pymysql
from scrapy.exceptions import CloseSpider


from Bill.util import misc
from scrapy.conf import settings
from Bill.items import RzlineItem
from Bill.util.send_email import EmailSender

Today = time.strftime("%Y%m%d")
Today1 = time.strftime("%Y-%m-%d")


class RzlineSpider(scrapy.Spider):
    name = 'rzline'
    allowed_domains = ['rzline.com']
    start_urls = ['http://www.rzline.com/web/front/quoteMarket/show']

    except_company = ['沃泉金融', '杭州沃泉金融', '杭州沃泉金融服务外包有限公司']

    custom_settings = {
        "LOG_LEVEL": "INFO",
        'LOG_FILE': os.path.join(settings['LOG_DIR'], name, Today + '.txt'),
        'DOWNLOADER_MIDDLEWARES': {
            'Bill.middlewares.RandomUserAgentMiddleware': 544,
            'Bill.middlewares.RzlineMiddleware': 546,
        }
    }

    city_list = [
                 '北京市', '哈尔滨市', '长春市', '沈阳市', '天津市',
                 '呼和浩特市', '乌鲁木齐市', '银川市', '西宁市', '兰州市', '西安市',
                 '拉萨市', '成都市', '重庆市', '贵阳市', '昆明市',
                 '太原市', '石家庄市', '济南市', '郑州市', '合肥市',
                 '南京市', '上海市', '武汉市',  '长沙市', '南昌市',
                 '杭州市', '福州市', '台北市'
                 '南宁市', '海口市', '广州市', '深圳市',
                 ]

    # 查询日期
    quoteDate = time.mktime(time.strptime(Today, '%Y%m%d'))
    quoteDate = str(quoteDate).replace('.', '') + '00'

    quoteType_dict = {
                      'e': '电票',
                      'se': '小电票',
                      # 's': '纸票',
                      # 'b': '商票',
                      }
    # 类型字典
    kind_dict = {'gg': '国股', 'sh': '城商', 'sn': '三农',
                 'busEle': '电子', 'busPaper': '纸质',
                 'gq': '国企', 'yq': '央企',
                 'ss': '上市公司', 'my': '民营企业'}
    # 业务类型字典
    busType_dict = {"1": "买断", "2": "直贴", "0": ""}

    # 查询条数
    rows = 100

    formdata = {
        "page": 1,
        "city": "",
        "rows": rows,
        "orderBy": "2",
        "quoteType": "",
        "detailType": "",
        "quoteDate": quoteDate,
        "appVersion": "iOS2.6.1",
        "ifDefaultCity": "false",
    }

    formdata1 = {
        "quoteDate": "",
        "quoteType": "",
        "orgUserId": "",
        "appVersion": "2.6.1",
    }

    headers = {
        "Content-Length": "82",
        "Host": "www.rzline.com",
        "Connection": "keep-alive",
        "Origin": "http://www.rzline.com",
        "Accept-Encoding": "gzip, deflate",
        "Accept-Language": "zh-CN,zh;q=0.9",
        "X-Requested-With": "XMLHttpRequest",
        "Content-Type": "application/json;charset=UTF-8",            # 必须添加
        "Accept": "application/json, text/javascript, */*; q=0.01",  # 必须添加
        "Referer": "http://www.rzline.com/web/front/quoteMarket/show",
    }

    # 连接数据库
    db = pymysql.connect(host='10.11.2.138', port=3306, user='sunhf', password='sunhf@345')
    cur = db.cursor()

    def parse(self, response):
        base_url = 'http://www.rzline.com/web/mobuser/market/quoteShow'
        for city in self.city_list:
            for type in self.quoteType_dict:
                formdata = copy.deepcopy(self.formdata)
                formdata['city'] = city
                formdata['quoteType'] = type
                if city == '上海市':
                    formdata['ifDefaultCity'] = 'true'
                    pass
                url = base_url + '&page=' + str(formdata['page'])
                yield scrapy.Request(
                    url=url,
                    dont_filter=True,
                    callback=self.parse_id,
                    errback=self.hand_error,
                    meta={'data': formdata, 'header': self.headers, 'city': city},
                )

    def parse_id(self, response):
        flag = 1
        city = response.meta['city']
        data = response.body.decode()
        json_data = json.loads(data)
        id_url = 'http://www.rzline.com/web/mobuser/market/quoteDetail'
        print('当前页数：{}'.format(response.meta['data']['page']))
        print('data=', response.meta['data'])
        try:
            data_list = json_data['data']
            if data_list:
                for i in data_list:
                    user_id = i['orgUserId']
                    company = i['orgSimpleName']
                    price_list = i['quotePriceDetailList'] if i['quotePriceDetailList'] else []

                    if len(price_list):
                        formdata1 = copy.deepcopy(self.formdata1)
                        formdata1['orgUserId'] = str(user_id)
                        formdata1['quoteDate'] = i['quoteDate']
                        formdata1['quoteType'] = response.meta['data']['quoteType']

                        url = id_url + '&orgUserId=' + str(user_id) + \
                            '&quoteType=' + formdata1['quoteType']

                        print(user_id, ':', company, ':', len(price_list),
                              ':', city, ':', formdata1['quoteType'])

                        self.logger.info(str(user_id)+':'+company+':'+str(len(price_list))
                                         + ':' + city + ':' + formdata1['quoteType'])

                        yield scrapy.Request(url=url,
                                             priority=1,
                                             callback=self.parse_detail,
                                             errback=self.hand_error,
                                             meta={'data': formdata1,
                                                   'city': city,
                                                   'header': self.headers,
                                                   'user_id': user_id,
                                                   'quoteType': formdata1['quoteType'],
                                                   }
                                             )
            else:
                flag = 0
        except Exception as e:
            # 发送邮件
            title = '爬虫' + self.name + '异常'
            error_info = misc.get_error_info(str(e))
            content = '异常位置：' + error_info['pos'] + '\n' + '异常原因：' + error_info['reason']
            EmailSender().send(title, content)
            raise CloseSpider
        # # 下一页: rows设置为100时，不需要下一页
        # if flag:
        #     # self.logger.debug('当前页数：{}'.format(response.meta['data']['page']))
        #     print('当前页数：{}'.format(response.meta['data']['page']))
        #     print('data=', response.meta['data'])
        #     formdata = response.meta['data']
        #     formdata['page'] += 1
        #     base_url = 'http://www.rzline.com/web/mobuser/market/quoteShow'
        #     url = base_url + '&page=' + str(formdata['page'])
        #     yield scrapy.Request(
        #                          url=url,
        #                          callback=self.parse_id,
        #                          errback=self.hand_error,
        #                          meta={'data': formdata,
        #                                'city': city,
        #                                'header': self.headers},
        #                         )

    def parse_detail(self, response):
        res = response.body.decode('utf-8')
        data = json.loads(res)
        data = data['data']

        price_list = data.get('quotePriceDetailList', [])

        if not price_list:
            print('formdata1:', response.meta['data'])
        else:
            print('city', response.meta['city'])
            for price in price_list:
                item = RzlineItem()
                try:
                    # 发布时间
                    F2 = price['createTime'] if price['createTime'] else None
                    F2 = F2.replace('-', '').replace(':', '').replace(' ', '') if F2 else ''
                    item['F2'] = F2

                    # 机构
                    # simple_name = data['orgInfoDto']['orgSimplename'] if data['orgInfoDto'] else ''
                    whole_name = data['orgInfoDto']['orgWholename'] if data['orgInfoDto'] else ''
                    item['F3'] = whole_name if whole_name else ''

                    # 金额
                    item['F4'] = price['price'] if price['price'] else ''

                    # 类型
                    detail_type = price['detailType'] if price['detailType'] else ''
                    quote_btype = price['quoteBType'] if price['quoteBType'] else ''
                    if detail_type in ['gg', 'sh', 'sn']:
                        kind = self.kind_dict[detail_type]
                    elif detail_type in ['busEle', 'busPaper']:
                        kind = self.kind_dict[quote_btype]
                    else:
                        kind = ''
                    item['F5'] = kind

                    # 每十万
                    F6 = price['tenInterest'].replace('--', '') if 'tenInterest' in price else ''
                    item['F6'] = F6 + '元' if F6 else ''

                    # 期限
                    F7 = price['quoteDays'] if price['quoteDays'] else ''
                    item['F7'] = F7

                    # 额度
                    item['F8'] = price['quoteAmount']

                    # 业务类型(买断、直贴)
                    item['F9'] = '直贴'

                    # 联系人
                    F10 = data['accountManagerList'][0]['name'] if data['accountManagerList'] else ''
                    item['F10'] = F10

                    # 联系方式
                    F11 = data['accountManagerList'][0]['mobPhone'] if data['accountManagerList'] else ''
                    item['F11'] = F11

                    item['F12'] = self.quoteType_dict[response.meta['quoteType']]

                    # 原始业务类型
                    item['F13'] = self.busType_dict[data['busType']] if data['busType'] else ''

                    # 唯一标识： 日期(年/月/日)+机构+类型+数量+期限+业务类型+电票
                    item['F1'] = self._get_uuid(item)

                    # FT, FV, FP, FU, FS
                    FS = data['ifStartTrad'] if data['ifStartTrad'] else None
                    item['FS'] = 0 if FS != "1" else 1

                    item['FP'] = int(time.strftime("%Y%m%d%H%M%S"))

                    item['FU'] = int(time.strftime("%Y%m%d%H%M%S"))

                    if item['F3'] in self.except_company:
                        return

                    if Today in item['F2']:
                        print('今日数据：')
                        print(item, response.meta['user_id'])
                        self.logger.info(item['F3']+':'+str(response.meta['user_id'])+':'+str(item['F2']))
                        yield item
                    else:
                        print('非今日的数据：')
                        F2 = '-'.join((item['F2'][:4], item['F2'][4:6], item['F2'][6:8]))
                        self.cur.execute("select f002_ths032 from pljr.ths032 "
                                         "where f003_ths032 = '212004' "
                                         "and f001_ths032 like '{}%'".format(F2))
                        day = self.cur.fetchone()[0]
                        start = time.mktime(time.strptime(item['F2'][:8], '%Y%m%d'))
                        next_day = time.strftime('%Y-%m-%d', time.localtime(start + (24*60*60)))
                        self.cur.execute("select f002_ths032 from pljr.ths032 "
                                         "where f003_ths032 = '212004' "
                                         "and f001_ths032 like '{}%'".format(next_day))
                        next = self.cur.fetchone()[0]
                        end = time.mktime(time.strptime(Today, '%Y%m%d'))
                        days = int(end - start) // (24 * 60 * 60)
                        if day == '1':
                            if days == 1 or (days == 3 and next == '2'):
                                t = item['F2'][8:]
                                if t > '165000':
                                    print(day, days, next)
                                    item['F2'] = Today + '080000'
                                    item['F1'] = self._get_uuid(item)
                                    print(item, response.meta['user_id'])
                                    yield item
                                    self.logger.info(
                                        item['F3'] + ':' + str(response.meta['user_id']) + ':' + str(item['F2']))
                        else:
                            if days <= 3:
                                item['F2'] = Today + '080000'
                                item['F1'] = self._get_uuid(item)
                                print(item, response.meta['user_id'])
                                yield item
                                self.logger.info(
                                    item['F3'] + ':' + str(response.meta['user_id']) + ':' + str(item['F2']))

                except Exception as e:
                    title = '爬虫' + self.name + '异常'
                    error_info = misc.get_error_info(str(e))
                    content = '异常位置：' + error_info['pos'] + '\n' + '异常原因：' + error_info['reason']
                    EmailSender().send(title, content)
                    raise CloseSpider

    @staticmethod
    def _get_uuid(item):
        # 唯一标识： 日期(年/月/日)+机构+类型+数量+期限+业务类型+电票
        uu_str = item['F2'][:8] + item['F3'] + item['F5'] + item['F7'] \
                 + item['F8'] + item['F13'] + item['F12']
        uu_id = misc.get_uuid(uu_str)
        return uu_id

    def hand_error(self, failture):
        print(failture)
