# -*- coding: utf-8 -*-
import scrapy
import time
from Bill.items import *
from Bill.util import misc
from Bill.util.misc import trace_error

Today = time.strftime("%Y%m%d")
Year = time.strftime("%Y")


class ShendupjSpider(scrapy.Spider):
    name = 'shendupj'
    allowed_domains = ['shendupiaoju.com']
    start_urls = ['http://www.shendupiaoju.com/inde_draft?pageSize=15&pageNo=0&today=1']

    custom_settings = {
        'LOG_LEVEL': 'DEBUG',
        'DOWNLOADER_MIDDLEWARES': {
            'Bill.middlewares.RandomUserAgentMiddleware': 544,
            # 'Bill.middlewares.RandomProxyMiddleware': 545,
        }
    }

    @trace_error
    def parse(self, response):
        values = response.xpath('//*[@id="count"]/@value').extract_first()
        print('总数量为：', values)
        if not values:
            print('出现异常')
            return
        page_size = 100
        pages = int(values) // page_size + 1
        print('总页数为：', pages)
        for page in range(1, pages+1):
            print('正在爬取第{}页'.format(page))
            url = 'http://www.shendupiaoju.com/inde_draft?pageSize={}&pageNo={}&today=1' \
                  '&draftType=&bankClassification=&expiryDateRange=&amtRange=&draftStatus='\
                  .format(page_size, page)

            yield scrapy.Request(url,
                                 callback=self.parse_detail,
                                 dont_filter=True,
                                 meta={'page': str(page)}
                                 )

    @trace_error
    def parse_detail(self, response):
        node_list = response.xpath('//tr')

        if not node_list:
            print('节点列表为空, 重新发送请求！')
            yield scrapy.Request(response.url,
                                 callback=self.parse_detail,
                                 dont_filter=True,
                                 meta={'page': response.meta['page']}
                                 )
            return

        n = 1
        for node in node_list:

            print('*' * 10, '第'+response.meta['page']+'页', n, '*' * 10)
            n += 1

            item = BillItem()

            F2 = node.xpath('td[1]/text()').extract_first()
            if F2:
                F2 = Year + F2.replace(' ', '').replace(':', '').replace('/', '') + '00'
            else:
                F2 = ''
            item['F2'] = F2

            today = item['F2'][:8]

            item['F3'] = None

            item['F4'] = '出'

            F5 = node.xpath('td[2]/span/following::text()').extract_first()
            if not F5:
                F5 = node.xpath('td[2]/text()').extract_first()
            if F5:
                F5 = F5.replace('\r\n', '').replace('\t', '')
            else:
                F5 = ''
            item['F5'] = F5

            F7_1 = node.xpath('td[4]/text()').extract_first()
            F7_2 = node.xpath('td[3]/text()').extract_first()
            if F7_1 and F7_2:
                F7 = F7_1 + ',' + F7_2
            elif F7_1:
                F7 = F7_1
            else:
                F7 = ''
            item['F7'] = F7

            F8 = node.xpath('td[5]/text()').extract_first()
            if F8:
                F8 = F8.replace(' ', '')
                F8 = '%.2f' % float(F8)
                F8 = str(F8) + '万'
            else:
                F8 = ''
            item['F8'] = F8

            F9 = node.xpath('td[6]/text()').extract_first()
            item['F9'] = F9 if F9 else ''

            if F9 and today:
                start = time.mktime(time.strptime(today, '%Y%m%d'))
                end = time.mktime(time.strptime(F9.replace('/', ''), '%Y%m%d'))
                F10 = int(end - start)//(24*60*60)
                F10 = str(F10) + '天'
            else:
                F10 = ''
            item['F10'] = F10

            if (item['F8'] and float(item['F8'].replace('万', '')) >= 100) \
                    or (item['F10'] and int(item['F10'].replace('天', '')) >= 190):
                item['F6'] = '电票'
            else:
                item['F6'] = ''

            item['F11'] = None

            F12 = node.xpath('td[7]/span/text()').extract_first()
            if F12:
                F12 = F12.replace('每十万扣款 ', '') + '元' if '竞价' not in F12 else F12
            else:
                F12 = ''
            item['F12'] = F12

            item['F13'] = ''

            item['F14'] = None

            uu_str = item['F5'] + item['F7'] + item['F8'] + item['F9'] + item['F12']
            uu_id = misc.get_uuid(uu_str)
            item['F1'] = uu_id

            # FT, FV, FP, FU, FS
            FS = ''.join(node.xpath('td[9]/text()').extract())
            item['FS'] = 0 if '交易成功' in FS or '竞价' in item['F12'] else 1

            item['FP'] = int(time.strftime("%Y%m%d%H%M%S"))

            item['FU'] = int(time.strftime("%Y%m%d%H%M%S"))

            print(item)
            yield item
