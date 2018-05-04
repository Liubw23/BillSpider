# coding=utf-8
import hashlib
import sys
import traceback
from Bill.util.send_email import EmailSender


def get_uuid(s):
    """
    通过md5摘要算法，给一个字符串对象生成唯一id
    :param s: 字符串
    :return: id
    """
    md5 = hashlib.md5()
    s_en = s.encode()
    md5.update(s_en)
    uu_id = md5.hexdigest()
    return uu_id


def get_error_info(e):
    """
    获取错误信息
    :param e: 错误原因
    :return: 错误信息
    """
    info = sys.exc_info()
    error_info = dict()

    if info[2]:

        for file, line_no, func, text in traceback.extract_tb(info[2]):
            pos = file + " line " + str(line_no) + " in " + "{" + text + "}"
            error_info['pos'] = pos
            error_info['reason'] = e

    else:

        error_info['pos'] = ''
        error_info['reason'] = ''

    return error_info


def trace_error(func):
    """
    a decorator for catching exception and sending email
    :param func:
    :return:
    """
    def wrap(*args, **kwargs):
        try:
            for i in func(*args, **kwargs):
                yield i
        except Exception as e:
            # send email
            name = str(func.__qualname__).split('.')[0]
            title = '{} is abnormal'.format(name)
            error_info = get_error_info(str(e))
            content = 'Exception position：' + error_info['pos'] + '\n' + 'Exception reason：' + error_info['reason']
            EmailSender().send(title, content)
            # stop spider
            from scrapy.exceptions import CloseSpider
            raise CloseSpider(e)
    return wrap


if __name__ == '__main__':
    pass
