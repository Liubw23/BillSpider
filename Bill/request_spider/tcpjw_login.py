import os
import time
import requests
from Bill.settings import FILE_DIR

Today = time.strftime("%Y%m%d")


def set_cookie():
    login_url = 'https://www.tcpjw.com/Account/Login'
    formdata = {
        "userName": "15902101576",
        "passWord": "pr123456",
    }

    res = requests.post(login_url, data=formdata, verify=False)
    cookie_jar = res.cookies
    cookies = requests.utils.dict_from_cookiejar(cookie_jar)
    cookie = ';'.join([i + '=' + cookies[i] for i in cookies])

    file_path = os.path.join(FILE_DIR, Today+'tcpjw_cookie.txt')
    try:
        with open(file_path, 'w') as f:
            f.write(cookie)
    except Exception as e:
        print(e)

    # headers = {
    #     "cookie": cookie,
    # }
    # data = {
    #     "pt_bid": "1",
    #     "pageIdx": "2",
    # }
    #
    # url = 'https://www.tcpjw.com/OrderList/TradingCenter'
    #
    # res1 = requests.post(url, data=data, headers=headers)
    # print(res1.text)


def get_cookie():
    file_path = os.path.join(FILE_DIR, Today+'tcpjw_cookie.txt')
    if not os.path.isfile(file_path):
        set_cookie()
    with open(file_path, 'r') as f:
        return f.read()


if __name__ == '__main__':
    # set_cookie()
    cookie = get_cookie()
    print(cookie)
    exit(0)
    headers = {
        "cookie": cookie,
    }
    data = {
        "pt_bid": "1",
        "pageIdx": "2",
    }

    url = 'https://www.tcpjw.com/OrderList/TradingCenter'

    res1 = requests.post(url, data=data, headers=headers, verify=False)
    print(res1.text)

