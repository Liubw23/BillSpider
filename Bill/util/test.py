import requests
import json

formdata1 = {
        "appVersion": "1.3.1",
        "orgUserId": "648",
        "quoteDate": "1524758400000",
        "quoteType": "s",
    }

cookie = "UM_distinctid=16300ec33eb94-0533f85f42763b-44480c2e-15f900-16300ec33ec23e; td_cookie=2204242325; Hm_lvt_0c9b71da7f914e3203b6d31569e26c11=1524728869,1524790659; CNZZDATA1257354179=1630177932-1524724860-%7C1524790562; Qs_lvt_32188=1524728870%2C1524790659; Qs_pv_32188=1552019861564832800%2C3227383852304174600%2C2203303578131011000%2C3729906259189132300%2C3564344308764102700; JSESSIONID=75EEE8E337698B6248749B9AB400B1F3; Hm_lvt_5de06b241236de21be8cbad7bd27c6d0=1524727347,1524789242,1524794654; Hm_lpvt_5de06b241236de21be8cbad7bd27c6d0=1524794654"

headers = {
    "Accept": "application/json, text/javascript, */*; q=0.01",
    "Accept-Encoding": "gzip, deflate",
    "Accept-Language": "zh-CN,zh;q=0.9",
    "Connection": "keep-alive",
    "Content-Length": "82",
    "Content-Type": "application/json;charset=UTF-8",
    "Cookie": cookie,
    "Host": "www.rzline.com",
    "Origin": "http://www.rzline.com",
    "Referer": "http://www.rzline.com/web/front/quoteMarket/show",
    "User-Agent": "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) "
                  "Chrome/66.0.3359.117 Safari/537.36",
    "X-Requested-With": "XMLHttpRequest"
}

url = 'http://www.rzline.com/web/mobuser/market/quoteDetail'
data = requests.post(url=url, data=json.dumps(formdata1), headers=headers)
print(data.text)
