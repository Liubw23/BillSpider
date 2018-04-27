# coding=utf-8
import hashlib
import sys
import traceback


def get_uuid(s):
    """
    通过md5摘要算法，给一个字符串对象生成唯一id
    :param s: 字符串
    :return: id
    """
    md5 = hashlib.md5()
    s_en = s.encode()
    md5.update(s_en)
    id = md5.hexdigest()
    return id


def get_error_info(e):
    """
    获取错误信息
    :param e: 错误原因
    :return: 错误信息
    """
    info = sys.exc_info()
    error_info = dict()

    if info[2]:

        for file, line_no, function, text in traceback.extract_tb(info[2]):
            pos = file + " line " + str(line_no) + " in " + "{" + text + "}"
            error_info['pos'] = pos
            error_info['reason'] = e

    else:

        error_info['pos'] = ''
        error_info['reason'] = ''

    return error_info


if __name__ == '__main__':
    print(get_uuid('霸州市农村信用合作联社,三农+1000.00万'))
