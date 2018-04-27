# coding=utf-8


class DatabaseException(Exception):
    def __init__(self, err='数据库错误'):
        Exception.__init__(self, err)


class EmptyNodeException(Exception):
    def __init__(self, error='节点为空!'):
        Exception.__init__(self, error)




