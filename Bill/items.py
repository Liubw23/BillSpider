# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# https://doc.scrapy.org/en/latest/topics/items.html

import scrapy


class BillItem(scrapy.Item):
    # define the fields for your item here like:
    # name = scrapy.Field()

    # 插入id, bigint
    FT = scrapy.Field()
    # 更新id, bigint
    FV = scrapy.Field()
    # 插入时间, bigint
    FP = scrapy.Field()
    # 更新时间, bigint
    FU = scrapy.Field()
    # 是否成交 1:未成交 0:成交, tinyint
    FS = scrapy.Field()

    # 原记录标识
    F1 = scrapy.Field()
    # 发布时间, bigint
    F2 = scrapy.Field()
    # 报价方, 即联系人
    F3 = scrapy.Field()
    # 方向, 默认为"出"
    F4 = scrapy.Field()
    # 种类, {(国股 大商 城商 三农 村镇):银票, (其它，财务):财票, (其它):商票}
    F5 = scrapy.Field()
    # 介质, 电票（金额>=100万，或期限>=190天）
    F6 = scrapy.Field()
    # 承兑人
    F7 = scrapy.Field()
    # 金额
    F8 = scrapy.Field()
    # 到期日
    F9 = scrapy.Field()
    # 期限
    F10 = scrapy.Field()
    # 价格(利率)
    F11 = scrapy.Field()
    # 价格(每十万贴息)
    F12 = scrapy.Field()
    # 原文, null
    F13 = scrapy.Field()
    # 联系方式
    F14 = scrapy.Field()


class RzlineItem(scrapy.Item):
    # 插入id, bigint
    FT = scrapy.Field()
    # 更新id, bigint
    FV = scrapy.Field()
    # 插入时间, bigint
    FP = scrapy.Field()
    # 更新时间, bigint
    FU = scrapy.Field()
    # 是否成交 1:未成交 0:成交, tinyint
    FS = scrapy.Field()

    # 原记录标识
    F1 = scrapy.Field()
    # 发布时间, bigint
    F2 = scrapy.Field()
    # 机构
    F3 = scrapy.Field()
    # 金额
    F4 = scrapy.Field()
    # 类型, {国股 城商 三农 每十万}
    F5 = scrapy.Field()
    # 每十万
    F6 = scrapy.Field()
    # 期限
    F7 = scrapy.Field()
    # 额度
    F8 = scrapy.Field()
    # 业务类型
    F9 = scrapy.Field()
    # 联系人
    F10 = scrapy.Field()
    # 联系方式
    F11 = scrapy.Field()
