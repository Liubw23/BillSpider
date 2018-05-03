import time
import os
import sched


# 被周期性调度触发的函数
def func():
    os.system("scrapy crawl shendupj")


def perform(inc, sche):
    sche.enter(inc, 0, perform, (inc, sche))
    func()    # 需要周期执行的函数


def main():
    # 初始化sched模块的scheduler类
    # 第一个参数是一个可以返回时间戳的函数，第二个参数可以在定时未到达之前阻塞。
    sche = sched.scheduler(time.time, time.sleep)
    interval = 60*30
    sche.enter(0, 0, perform, (interval, sche))
    sche.run()  # 开始运行，直到计划时间队列变成空为止


if __name__ == "__main__":

    start_time = time.time()

    main()






