import time
import os
from scrapy import cmdline
import sys
import sched
from multiprocessing import Pool


def func(spider):
    os.system("scrapy crawl {}".format(spider))


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

    spiders = ['shendupj', 'rzline', 'exbill']

    p = Pool(len(spiders))

    for spider in spiders:
        p.apply_async(main, args=(spider,))

    p.close()
    p.join()






