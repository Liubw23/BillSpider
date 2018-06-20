import time
import os
import sys
import sched


def func(spider):
    os.system("scrapy crawl {}".format(spider))
    print('*'*100)


def perform(inc, sche, spider):
    sche.enter(inc, 0, perform, (inc, sche, spider))
    func(spider)    # 需要周期执行的函数


def main(spider):
    sche = sched.scheduler(time.time, time.sleep)
    interval = 60*30
    sche.enter(0, 0, perform, (interval, sche, spider))
    sche.run()  # 开始运行，直到计划时间队列变成空为止


if __name__ == "__main__":

    start_time = time.time()

    try:
        spider = sys.argv[1]
    except Exception as e:
        print('正确启动格式：python start.py 爬虫名')
        spider = input('请输入爬虫名：')
    main(spider)







