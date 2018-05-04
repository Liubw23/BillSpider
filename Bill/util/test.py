import requests
import json
import time


formdata1 = {
        "appVersion": "1.3.1",
        "orgUserId": "2520",
        "quoteDate": "",
        "quoteType": "",
    }

formdata = {
        "appVersion": "web1.1.0",
        "city": "全国",
        "detailType": "",
        "ifDefaultCity": "true",
        "orderBy": "2",
        "page": 1,
        "quoteDate": "1524758400000",
        "quoteType": "e",
        "rows": 7
    }


headers = {
        "Accept": "application/json, text/javascript, */*; q=0.01",  # 必须添加
        "Content-Type": "application/json;charset=UTF-8",            # 必须添加
        "Accept-Encoding": "gzip, deflate",
        "Accept-Language": "zh-CN,zh;q=0.9",
        "Connection": "keep-alive",
        "Content-Length": "84",
        "Host": "app.rzline.com",
        "cookies": "Qs_lvt_32188=1524728870%2C1524790659; ",
        "Origin": "http://www.rzline.com",
        "Referer": "http://www.rzline.com/web/front/quoteMarket/show",
        "X-Requested-With": "XMLHttpRequest",
        "User-Agent": "QunChangMob/2.6.1 (iPhone; iOS 11.1.1; Scale/2.00)",

}

url = 'http://www.rzline.com/web/mobuser/market/quoteShow'
response = requests.post(url=url, data=json.dumps(formdata), headers=headers)
data = json.loads(response.text)
# print(data['data'])

values = []
# for i in data['data']:
#     print(i['orgUserId'])
#     values.append(i['orgUserId'])
#
# v_set = set(values)
# print(len(v_set))

# ***************************************************************************
Today = time.strftime("%Y%m%d")
quoteDate = time.mktime(time.strptime(Today, '%Y%m%d'))
quoteDate = str(quoteDate).replace('.', '') + '00'
formdata1 = {
        "appVersion": "2.6.1",
        "orgUserId": "2095",
        "quoteDate": 1525276800000,
        "quoteType": "b",
    }

header1={
"Accept": "*/*",
# "Accept-Encoding": "gzip, deflate",
# "Accept-Language": "zh-Hans-CN;q=1, fr-FR;q=0.9",
# "User-Agent": "QunChangMob/2.6.1 (iPhone; iOS 11.1.1; Scale/2.00)",
# "X-Requested-With": "XMLHttpRequest",
# "Content-Length": "84",
"Content-Type": "application/json",
# "Host": "www.rzline.com",
# "Connection": "keep-alive",
}
# data1 = {"orgUserId":"1288", "quoteDate":'', "quoteType":"", "appVersion":"2.6.1"}
url = 'http://www.rzline.com/web/mobuser/market/quoteDetail'
response = requests.post(url=url, data=json.dumps(formdata1), headers=headers)
data = json.loads(response.text)
data =data['data']
data=data['quotePriceDetailList']
print(data)


