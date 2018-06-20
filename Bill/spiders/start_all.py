import os
import time
import sched
from multiprocessing import Pool


def func(spider):
    os.system("scrapy crawl {} --nolog".format(spider))
    print('*'*50, spider, '*'*50)


def perform(inc, sche, spider):
    sche.enter(inc, 0, perform, (inc, sche, spider))
    func(spider)    # 需要周期执行的函数


def main(spider):
    try:
        sche = sched.scheduler(time.time, time.sleep)
        interval = 60*60
        sche.enter(0, 0, perform, (interval, sche, spider))
        sche.run()  # 开始运行，直到计划时间队列变成空为止
    except KeyboardInterrupt:
        print('退出当前进程！')
        exit(0)


if __name__ == "__main__":
    try:
        start_time = time.time()

        spiders = ['exbill', 'rzline', 'shendupj', 'tcpjw', 'zaopiaowang', 'pttkj', 'huipiaoxian', 'cpiaoju']

        p = Pool(len(spiders))

        for spider in spiders:
            p.apply_async(main, args=(spider,))

        p.close()
        p.join()
    except Exception as e:
        print(e)






