import json
import time
import requests
import pymysql
import datetime


class QeubeeMoneyMarket(object):

    def __init__(self):

        self.conn = pymysql.connect(host='10.10.128.116', user='root', password='111111', db='pdb', charset='utf8')
        self.cur = self.conn.cursor()
        self.items = self.get_items('P14004')

    def get_items(self, table):
        self.cur.execute(r"""select F1 from {}""".format(table))
        items = self.cur.fetchall()
        items = [i[0] for i in items]
        return items

    def get_data(self):
        headers = {
            "Host": "money-market.idbhost.com",
            "Accept": "application/json",
            "Accept-Language": "zh-cn",
            "Accept-Encoding": "gzip, deflate",
            "password": "7f19bd35cff8da8827997cbb1f959b82",
            "Content-Type": "application/json",
            "Origin": "http://moneymarketmobile.idbhost.com",
            "Connection": "keep-alive",
            "username": "konghesmileface@gmail.com",
            "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 11_1_1 like Mac OS X) AppleWebKit/604.3.5 (KHTML, like Gecko) "
                          "Mobile/15B150",
            "Referer": "http://moneymarketmobile.idbhost.com/?username=konghesmileface@gmail.com"
                       "&pwd=7f19bd35cff8da8827997cbb1f959b82&version=1.2.0",

        }

        url = 'http://money-market.idbhost.com/money_market/mobile/queryQuoteMain'

        kind_list = ['GTF', 'UR2', 'UR3']

        for kind in kind_list:
            data = '{"direction": "OUT", "quoteType": "' + kind + '", "areas": [], "institutionScaleLow": 0, \
                "institutionScaleHigh": 9999999999999, "tagCodes": []}'

            print(data)

            res = requests.post(url, headers=headers, data=data)

            print(res)

            data_list = json.loads(res.text)['result']

            for data in data_list:
                for i in data['quoteDetailsDtos']:
                    item = dict()
                    item['F1'] = i['id']
                    item['F2'] = data['institutionName']
                    item['F3'] = data['quoteType']
                    item['F4'] = data['fundSize']
                    item['F5'] = data['direction']
                    item['F6'] = i['quoteTimePeriod']
                    item['F7'] = i['price']
                    item['F8'] = data['trader']['name']
                    item['F9'] = data['trader']['telephone']
                    item['F10'] = data['trader']['mobile']
                    item['F11'] = data['trader']['email']
                    item['F12'] = data['memo']

                    item['FS'] = 1 if data['active'] else 0
                    item['FP'] = int(time.strftime("%Y%m%d%H%M%S"))
                    item['FU'] = int(time.strftime("%Y%m%d%H%M%S"))
                    print(item)
                    self.save_data(item)

                print('\r\n')

    def save_data(self, item):
        try:
            if item['F1'] not in self.items:
                print('插入数据...')
                self.cur.execute(r'''insert into P14004
                                     values(
                                     UNIX_TIMESTAMP(CURRENT_TIMESTAMP)<<32 | RIGHT(UUID_SHORT(),8),
                                     UNIX_TIMESTAMP(CURRENT_TIMESTAMP)<<32 | RIGHT(UUID_SHORT(),8),
                                     %s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)''',
                                 [item['F1'], item['F2'], item['F3'], item['F4'], item['F5'],
                                  item['F6'], item['F7'], item['F8'], item['F9'], item['F10'],
                                  item['F11'], item['F12'], item['FS'], item['FP'], item['FU']])
            else:
                print('更新数据')
                self.cur.execute(r"""update P14004 set 
                                     FV=UNIX_TIMESTAMP(CURRENT_TIMESTAMP)<<32 | RIGHT(UUID_SHORT(),8),
                                     F2=%s, F3=%s, F4=%s, F5=%s, F6=%s, F7=%s, F8=%s,   
                                     F9=%s, F10=%s, F11=%s, F12=%s, FS=%s, FU=%s where F1=%s""",
                                 [item['F2'], item['F3'], item['F4'], item['F5'],
                                  item['F6'], item['F7'], item['F8'], item['F9'],
                                  item['F10'], item['F11'], item['F12'], item['FS'],
                                  datetime.datetime.now().strftime('%Y%m%d%H%M%S'), item['F1']])
            self.conn.commit()
        except Exception as e:
            print('插入失败原因：', e)

    def __exit__(self):
        self.cur.close()
        self.conn.close()


def main():
    qeubee = QeubeeMoneyMarket()
    qeubee.get_data()


if __name__ == '__main__':
    main()
