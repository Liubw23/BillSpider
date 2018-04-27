# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://doc.scrapy.org/en/latest/topics/item-pipeline.html
from .items import *
import pymysql
from scrapy.conf import settings
import datetime

class BillPipeline(object):
    def __init__(self):
        self.mysql_host = settings["MYSQL_HOST"]
        self.mysql_user = settings["MYSQL_USER"]
        self.mysql_pwd = settings["MYSQL_PWD"]
        self.mysql_db_name = settings["MYSQL_DB_NAME"]

    def open_spider(self, spider):
        self.db = pymysql.connect(self.mysql_host, self.mysql_user, self.mysql_pwd, self.mysql_db_name,
                                  charset='utf8')
        self.cur = self.db.cursor()
        self.items = self.get_items()

    def get_items(self):
        self.cur.execute(r"""select F1 from P14002""")
        items = self.cur.fetchall()
        items = [i[0] for i in items]
        return items

    def process_item(self, item, spider):
        if isinstance(item, BillItem):
            table = settings['MYSQL_TABLE']

            try:
                if item['F1'] not in self.items:
                    print('插入数据...')
                    self.cur.execute(r'''insert into P14002
                                         values(
                                         UNIX_TIMESTAMP(CURRENT_TIMESTAMP)<<32 | RIGHT(UUID_SHORT(),8),
                                         UNIX_TIMESTAMP(CURRENT_TIMESTAMP)<<32 | RIGHT(UUID_SHORT(),8),
                                         %s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)''',
                                         [item['F1'], item['F2'], item['F3'], item['F4'], item['F5'],
                                          item['F6'], item['F7'], item['F8'], item['F9'], item['F10'],
                                          item['F11'], item['F12'], item['F13'], item['F14'],
                                          item['FS'], item['FP'], item['FU']])
                else:
                    print('更新数据')
                    self.cur.execute(r"""update P14002 set 
                                         FV=UNIX_TIMESTAMP(CURRENT_TIMESTAMP)<<32 | RIGHT(UUID_SHORT(),8),
                                         F2=%s, F3=%s, F4=%s, F5=%s, F6=%s, F7=%s, F8=%s,   
                                         F9=%s, F10=%s, F11=%s, F12=%s, F13=%s, F14=%s, FS=%s, FU=%s
                                         where F1=%s""",
                                         [item['F2'], item['F3'], item['F4'], item['F5'],
                                          item['F6'], item['F7'], item['F8'], item['F9'], item['F10'],
                                          item['F11'], item['F12'], item['F13'], item['F14'], item['FS'],
                                          datetime.datetime.now().strftime('%Y%m%d%H%M%S'), item['F1']])
                self.db.commit()
            except Exception as e:
                print('插入失败原因：', e)
