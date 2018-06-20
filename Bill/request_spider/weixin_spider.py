import itchat
from itchat.content import *
import requests.api
import urllib3

msg_type_list = [TEXT, MAP, CARD, NOTE, SHARING, PICTURE, RECORDING, ATTACHMENT, VIDEO, FRIENDS, SYSTEM]


def requestspatch(method, url, **kwargs):
    """
    全局打补丁：将requests的verify为False
    :param method:
    :param url:
    :return:
    """
    kwargs['verify'] = False
    return _origcall(method, url, **kwargs)


@itchat.msg_register([TEXT])
def test_send(msg):
    res = itchat.search_friends(userName=msg['FromUserName'])['NickName'] + ':' + msg['Text']
    print('>>>', res)


@itchat.msg_register([TEXT], isGroupChat=True)
def gchat(msg):
    group_name = msg['User']['NickName']
    gres = (group_name + '~ ' + msg['ActualNickName'] + " : " + msg['Text'])
    print(gres)


if __name__ == '__main__':

    # 禁用urllib3警告
    urllib3.disable_warnings()

    _origcall = requests.api.request
    requests.api.request = requestspatch

    # 登录微信
    itchat.auto_login(hotReload=True)
    try:
        itchat.run()
    except Exception as e:
        print('e:', e)
        itchat.logout()
