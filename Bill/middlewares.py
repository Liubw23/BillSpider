# -*- coding: utf-8 -*-

# Define here the models for your spider middleware
#
# See documentation in:
# https://doc.scrapy.org/en/latest/topics/spider-middleware.html

import scrapy
from scrapy import signals
import random
import requests
import json
import time
import pymysql
from scrapy.http import HtmlResponse

from .settings import USER_AGENT_LIST


class BillSpiderMiddleware(object):
    # Not all methods need to be defined. If a method is not defined,
    # scrapy acts as if the spider middleware does not modify the
    # passed objects.

    @classmethod
    def from_crawler(cls, crawler):
        # This method is used by Scrapy to create your spiders.
        s = cls()
        crawler.signals.connect(s.spider_opened, signal=signals.spider_opened)
        return s

    def process_spider_input(self, response, spider):
        # Called for each response that goes through the spider
        # middleware and into the spider.

        # Should return None or raise an exception.
        return None

    def process_spider_output(self, response, result, spider):
        # Called with the results returned from the Spider, after
        # it has processed the response.

        # Must return an iterable of Request, dict or Item objects.
        for i in result:
            yield i

    def process_spider_exception(self, response, exception, spider):
        # Called when a spider or process_spider_input() method
        # (from other spider middleware) raises an exception.

        # Should return either None or an iterable of Response, dict
        # or Item objects.
        pass

    def process_start_requests(self, start_requests, spider):
        # Called with the start requests of the spider, and works
        # similarly to the process_spider_output() method, except
        # that it doesn’t have a response associated.

        # Must return only requests (not items).
        for r in start_requests:
            yield r

    def spider_opened(self, spider):
        spider.logger.info('Spider opened: %s' % spider.name)


class BillDownloaderMiddleware(object):
    # Not all methods need to be defined. If a method is not defined,
    # scrapy acts as if the downloader middleware does not modify the
    # passed objects.

    @classmethod
    def from_crawler(cls, crawler):
        # This method is used by Scrapy to create your spiders.
        s = cls()
        crawler.signals.connect(s.spider_opened, signal=signals.spider_opened)
        return s

    def process_request(self, request, spider):
        # Called for each request that goes through the downloader
        # middleware.

        # Must either:
        # - return None: continue processing this request
        # - or return a Response object
        # - or return a Request object
        # - or raise IgnoreRequest: process_exception() methods of
        #   installed downloader middleware will be called
        return None

    def process_response(self, request, response, spider):
        # Called with the response returned from the downloader.

        # Must either;
        # - return a Response object
        # - return a Request object
        # - or raise IgnoreRequest
        return response

    def process_exception(self, request, exception, spider):
        # Called when a download handler or a process_request()
        # (from other downloader middleware) raises an exception.

        # Must either:
        # - return None: continue processing this exception
        # - return a Response object: stops process_exception() chain
        # - return a Request object: stops process_exception() chain
        pass

    def spider_opened(self, spider):
        spider.logger.info('Spider opened: %s' % spider.name)


class RandomUserAgentMiddleware(object):

    def process_request(self, request, spider):
        user_agent = random.choice(USER_AGENT_LIST)
        # print('用户头：', user_agent)
        request.headers['User-Agent'] = user_agent


class RandomProxyMiddleware(object):

    def __init__(self):
        self.db = pymysql.connect('localhost', 'root', '1234', 'bill', charset='utf8')
        self.cur = self.db.cursor()

    def process_request(self, request, spider):
        self.cur.execute(r"""select * from proxys WHERE speed < 5 order by rand() LIMIT 1""")
        proxy = self.cur.fetchone()
        ip, port = proxy[1], proxy[2]
        proxys = str(ip) + ':' + str(port)
        print('proxy：', proxys, proxy[5])
        request.meta['proxy'] = r'http://' + proxys

    def process_response(self, request, response, spider):
        print('状态：', response.status)
        if response.status != 200:
            proxy = request.meta['proxy']
            print('无效的proxy: ', proxy)
            self._delete_proxy(proxy)
            return request
        else:
            return response

    def process_exception(self, request, exception, spider):
        print("this request {}'s exception is {}".format(request, exception))

    def _delete_proxy(self, proxy):
        ip_port = proxy.split('//')[1]
        ip, port = ip_port.split(':')
        self.cur.execute('delete from proxys where `ip`="{ip}" and `port`="{port}"'.format(ip=ip, port=port))
        self.db.commit()

    def spider_closed(self, spider):
        self.cur.close()
        self.db.close()


class RzlineMiddleware(object):

    def process_request(self, request, spider):

        if 'rzline' not in spider.name:
            return
        url_list = [
                    'http://www.rzline.com/web/mobuser/market/quoteShow',
                    'http://www.rzline.com/web/mobuser/market/quoteDetail',
                   ]

        for url in url_list:
            if url in request.url:

                data = request.meta['data']
                header = request.meta['header']
                info = self._post(url, header, data)
                return HtmlResponse(request.url,
                                    encoding='utf-8',
                                    body=info,
                                    request=request)

    @staticmethod
    def _post(url, header, data):
        response = requests.post(
                                 url=url,
                                 headers=header,
                                 data=json.dumps(data),
                                )
        response = response.content
        return response


class TcpjwMiddleware(object):

    def process_request(self, request, spider):

        if spider.name != 'tcpjw':
            return
        url = 'https://www.tcpjw.com/OrderList/TradingCenter'
        if url in request.url:
            proxys = request.meta['proxy'] if 'proxy' in request.meta else None
            data = request.meta['data']
            header = request.meta['header']
            info = self._post(url, header, data, proxys)
            return HtmlResponse(request.url,
                                encoding='utf-8',
                                body=info,
                                request=request)

    @staticmethod
    def _post(url, header, data, proxy):
        import urllib3
        urllib3.disable_warnings()
        proxies = {
            "http": "http://" + proxy.split('//')[1],
            "https": "https://" + proxy.split('//')[1],
        } if proxy else {}
        # print('requests post proxies: ', proxies)
        response = requests.post(
                                 url=url,
                                 headers=header,
                                 data=data,
                                 verify=False,
                                 proxies=proxies
                                )
        response = response.content
        return response
