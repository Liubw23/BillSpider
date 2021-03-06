# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://doc.scrapy.org/en/latest/topics/item-pipeline.html
from .items import *
import pymysql
import time
import datetime
from twisted.enterprise import adbapi
import pymysql.cursors

from scrapy.conf import settings

Today = time.strftime("%Y%m%d")


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
        self.items = self.get_items('P14002')
        self.rzline_items = self.get_items('P14003')
        self.s_values = set()
        self.rzline_s_values = set()

    def get_items(self, table):
        if table == "P14003":
            try:
                self.cur.execute(r"""select F1 from {} where F2 like '{}%'""".format(table, Today))
            except Exception as e:
                print('查询出错', e)
        else:
            self.cur.execute(r"""select F1 from {}""".format(table))
        items = self.cur.fetchall()
        items = sorted([i[0] for i in items])
        print('len(items)=', len(items))
        return items

    def process_item(self, item, spider):
        if isinstance(item, BillItem):

            try:

                if item['F1'] not in self.items and item['F1'] not in self.s_values:
                    self.s_values.add(item['F1'])
                    print('插入数据', item['F1'])
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
                    print('更新数据', item['F1'])
                    self.cur.execute(r"""update P14002 set 
                                         FV=UNIX_TIMESTAMP(CURRENT_TIMESTAMP)<<32 | RIGHT(UUID_SHORT(),8),
                                         F2=%s, F3=%s, F4=%s, F5=%s, F6=%s, F7=%s, F8=%s,   
                                         F9=%s, F10=%s, F11=%s, F12=%s, F13=%s, F14=%s, FS=%s, FU=%s
                                         where F1=%s""",
                                         [item['F2'], item['F3'], item['F4'], item['F5'],
                                          item['F6'], item['F7'], item['F8'], item['F9'], item['F10'],
                                          item['F11'], item['F12'], item['F13'], item['F14'], item['FS'],
                                          datetime.datetime.now().strftime('%Y%m%d%H%M%S'), item['F1']
                                          ])
                    #  and F2 like %s ,     "'{}%'".format(Today)
                self.db.commit()
            except Exception as e:
                print('失败原因：', e)

        elif isinstance(item, RzlineItem):
            try:
                if item['F1'] not in self.rzline_items and item['F1'] not in self.rzline_s_values:
                    self.rzline_s_values.add(item['F1'])
                    print('插入数据', item['F1'])
                    self.cur.execute(r'''insert into P14003
                                         values(
                                         UNIX_TIMESTAMP(CURRENT_TIMESTAMP)<<32 | RIGHT(UUID_SHORT(),8),
                                         UNIX_TIMESTAMP(CURRENT_TIMESTAMP)<<32 | RIGHT(UUID_SHORT(),8),
                                         %s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)''',
                                         [item['F1'], item['F2'], item['F3'], item['F4'], item['F5'],
                                          item['F6'], item['F7'], item['F8'], item['F9'], item['F10'],
                                          item['F11'], item['F12'], item['F13'], item['FS'], item['FP'], item['FU']])
                elif item['F1'] not in self.rzline_items and item['F1'] in self.rzline_s_values:
                    print('更新数据', item['F1'])
                    # 只更新当天数据
                    self.cur.execute(r"""update P14003 set 
                                         FV=UNIX_TIMESTAMP(CURRENT_TIMESTAMP)<<32 | RIGHT(UUID_SHORT(),8),
                                         F2=%s, F3=%s, F4=%s, F5=%s, F6=%s, F7=%s, F8=%s,   
                                         F9=%s, F10=%s, F11=%s, F12=%s, F13=%s, FS=%s, FU=%s
                                         where F1=%s and F2 like %s""",
                                     [item['F2'], item['F3'], item['F4'], item['F5'],
                                      item['F6'], item['F7'], item['F8'], item['F9'],
                                      item['F10'], item['F11'], item['F12'], item['F13'], item['FS'],
                                      datetime.datetime.now().strftime('%Y%m%d%H%M%S'), item['F1'],
                                      "'{}%'".format(Today)])
                self.db.commit()

                # 更改F9
                self.cur.execute('select * from P14003 where F3=%s and F12=%s and F2 like %s',
                                 [item['F3'], item['F12'], "'{}%'".format(Today)])
                count = len(self.cur.fetchone()) if self.cur.fetchone() else 0
                print('len(count)=', count)
                if count > 0:
                    self.cur.execute(r"""update P14003 set
                                         FV=UNIX_TIMESTAMP(CURRENT_TIMESTAMP)<<32 | RIGHT(UUID_SHORT(),8),
                                         F9=F13, FU=%s
                                         where F3=%s and F12=%s and F2 like %s""",
                                     [datetime.datetime.now().strftime('%Y%m%d%H%M%S'),
                                      item['F3'], item['F12'], "'{}%'".format(Today)])
                    self.db.commit()

            except Exception as e:
                print('失败原因：', e)

    def close_spider(self, spider):
        self.cur.close()
        self.db.close()


class TwistedBillPipeline(object):

    def __init__(self, dbpool):
        self.dbpool = dbpool
        self.mysql_host = settings["MYSQL_HOST"]
        self.mysql_user = settings["MYSQL_USER"]
        self.mysql_pwd = settings["MYSQL_PWD"]
        self.mysql_db_name = settings["MYSQL_DB_NAME"]

    def open_spider(self, spider):
        self.db = pymysql.connect(self.mysql_host, self.mysql_user, self.mysql_pwd, self.mysql_db_name,
                                  charset='utf8')
        self.cur = self.db.cursor()
        self.items = self._get_items()

    def _get_items(self):
        self.cur.execute(r"""select F1 from P14002""")
        items = self.cur.fetchall()
        items = [i[0] for i in items]
        return items

    @classmethod
    def from_settings(cls, settings):

        dbpool = adbapi.ConnectionPool(
                                       "pymysql",
                                       host=settings["MYSQL_HOST"],
                                       user=settings["MYSQL_USER"],
                                       password=settings["MYSQL_PWD"],
                                       db=settings["MYSQL_DB_NAME"],
                                       charset="utf8",
                                       cursorclass=pymysql.cursors.DictCursor,
                                       use_unicode=True
                                     )
        return cls(dbpool)

    def process_item(self, item, spider):
        # 使用twisted将mysql插入变成异步执行
        self.dbpool.runInteraction(self.do_insert, item)

    def do_insert(self, cursor, item):
        # 执行具体的插入
        # 根据不同的item 构建不同的sql语句并插入到mysql中
        try:
            if item['F1'] not in self.items:

                print('插入数据...')
                cursor.execute(r'''insert into P14002
                                   values(
                                   UNIX_TIMESTAMP(CURRENT_TIMESTAMP)<<32 | RIGHT(UUID_SHORT(),8),
                                   UNIX_TIMESTAMP(CURRENT_TIMESTAMP)<<32 | RIGHT(UUID_SHORT(),8),
                                   %s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)''',
                                   [item['F1'], item['F2'], item['F3'], item['F4'], item['F5'],
                                    item['F6'], item['F7'], item['F8'], item['F9'], item['F10'],
                                    item['F11'], item['F12'], item['F13'], item['F14'],
                                    item['FS'], item['FP'], item['FU']])

            else:
                print('更新数据...')
                cursor.execute(r"""update P14002 set 
                                   FV=UNIX_TIMESTAMP(CURRENT_TIMESTAMP)<<32 | RIGHT(UUID_SHORT(),8),
                                   F2=%s, F3=%s, F4=%s, F5=%s, F6=%s, F7=%s, F8=%s,   
                                   F9=%s, F10=%s, F11=%s, F12=%s, F13=%s, F14=%s, FS=%s, FU=%s
                                   where F1=%s""",
                                   [item['F2'], item['F3'], item['F4'], item['F5'],
                                    item['F6'], item['F7'], item['F8'], item['F9'], item['F10'],
                                    item['F11'], item['F12'], item['F13'], item['F14'], item['FS'],
                                    datetime.datetime.now().strftime('%Y%m%d%H%M%S'), item['F1']])
        except Exception as e:
            print('插入失败原因：', e)
