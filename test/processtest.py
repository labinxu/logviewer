import multiprocessing
import time
def worker(d, key, value):
    d[key] = value

def reader(d):
    while True:
        for k ,v in dict(d).items():
            print(k)
        time.sleep(1)

if __name__ == '__main__':
    mgr = multiprocessing.Manager()
    d = mgr.dict()
    jobs = [ multiprocessing.Process(target=worker, args=(d, i, i*2))
             for i in range(10) 
             ]
    p = multiprocessing.Process(target=reader, args=(d,))
    p.start()

    for j in jobs:
        j.start()

    for j in jobs:
        j.join()
    p.join()

    print ('Results:' )
