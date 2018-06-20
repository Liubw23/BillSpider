from websocket import create_connection
from multiprocessing import Pool, Manager
import json
import time
import pymysql
import datetime
import requests
import re


today = time.strftime('%Y%m%d', time.localtime(time.time()))
values = set()
items = list()
try:
    conn = pymysql.connect(host='10.10.96.134', user='root', password='111111', db='pdb', charset='utf8')
    cur = conn.cursor()
    cur.execute("select F1, F9, F11 from P14005 where F11='{}'".format(today))
    items = cur.fetchall()
except Exception as e:
    print('connect mysql error:', e)
items = [''.join(i) for i in items]
print(items)

f_set = set(items)


def get_token():
    index_url = 'https://www.tongyeyun.com/topfit/creditsSecondary/allBond/1'
    cookies = {
        "JSESSIONID": "B79CEEEB57533FC97481A8714D65DEE3"
    }
    res = requests.get(index_url, cookies=cookies)
    token_compile = re.compile(r'initWebsocket\(\"wss://www.tongyeyun.com/ws\", \"(.*?)\"')
    token = token_compile.search(res.text)
    token = token.group(1) if token else ''
    return token


token = get_token()


def get_data(q):
    global token
    print('token is:', token)
    if not token:
        print('没有登录！')
        q.put(0)
        return
    # websocket
    url = "wss://www.tongyeyun.com/ws"
    tokens = {"token": "{}".format(token), "biz": "bond_quote"}

    time_out = 120
    ws = create_connection(url, timeout=time_out)
    ws.send(json.dumps(tokens))  # 发送消息头

    heart_beat_times = 5
    n = 0
    while True:
        try:
            data = ws.recv()
            q.put(data)
        except:
            ws.close()
            get_data(q)


def read_data(q):
    while True:
        data = q.get()
        if data == 0:
            return

        if '"success":true' in data:
            json_data = json.loads(data)
            try:
                data = json_data['obj']['data']
                item = dict()
                item['F1'] = str(data['tradeId'])
                item['F2'] = data['shortName']
                item['F3'] = data['compName']
                item['F4'] = data['bondType']
                item['F5'] = str(data['remainPeriod']) + '天'
                item['F6'] = data['issueCreditRating']
                item['F7'] = str(data['volume']) + '万'
                item['F8'] = data['mdEntryPx']
                item['F9'] = 'BID' if 'bid' in data['memo'] else 'OFR'
                item['F10'] = data['memo']
                item['F11'] = time.strftime('%Y%m%d', time.localtime(int(str(data['createTime'])[:-3])))
                item['FP'] = int(time.strftime("%Y%m%d%H%M%S"))
                item['FU'] = int(time.strftime("%Y%m%d%H%M%S"))
                print(item)

                if item['F1'] + item['F9'] + item['F11'] not in f_set:
                    insert_data(item)
                    f_set.add(item['F1'] + item['F9'] + item['F11'])
                else:
                    update_data(item)
                
            except Exception as e:
                print('error:', e)
        elif '"success":false' in data:
            print('token 过期')
        else:
            print('recv >>> ', data)


def insert_data(item):
    try:
        print('插入数据{}'.format((item['F1'], item['F9'], item['F11'])))
        cur.execute(r'''insert into P14005
                        values(
                        UNIX_TIMESTAMP(CURRENT_TIMESTAMP)<<32 | RIGHT(UUID_SHORT(),8),
                        UNIX_TIMESTAMP(CURRENT_TIMESTAMP)<<32 | RIGHT(UUID_SHORT(),8),
                        %s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)''',
                        [item['F1'], item['F2'], item['F3'], item['F4'], item['F5'],
                         item['F6'], item['F7'], item['F8'], item['F9'], item['F10'],
                         item['F11'], item['FP'], item['FU']])
        conn.commit()
    except Exception as e:
        print('失败原因：', e)
        

def update_data(item):
    try:
        print('更新数据{}'.format((item['F1'], item['F9'], item['F11'])))
        cur.execute(r"""update P14005 set 
                        FV=UNIX_TIMESTAMP(CURRENT_TIMESTAMP)<<32 | RIGHT(UUID_SHORT(),8),
                        F2=%s, F3=%s, F4=%s, F5=%s, F6=%s, F7=%s, F8=%s,   
                        F10=%s, FU=%s where F1=%s and F9=%s and F11=%s""",
                        [item['F2'], item['F3'], item['F4'], item['F5'],
                         item['F6'], item['F7'], item['F8'], item['F10'],
                         datetime.datetime.now().strftime('%Y%m%d%H%M%S'),
                         item['F1'], item['F9'], item['F11']])
        conn.commit()
    except Exception as e:
        print('失败原因：', e)


def main():
    manager = Manager()
    q = manager.Queue()
    p = Pool()
    p.apply_async(get_data, args=(q,))
    p.apply_async(read_data, args=(q,))
    p.close()
    p.join()
    cur.close()
    conn.close()


if __name__ == '__main__':
    main()
