from threading import Thread, Lock
from Queue import Queue

thread = True
exit_flag = 0
lock = Lock()
task_queue = Queue()

def start_threading(**kwargs):
    global lock, task_queue, exit_flag
    hosts = kwargs['hosts']
    max_threads = kwargs['max_threads']
    if len(hosts) < max_threads:
        max_threads = len(hosts)

    #set thread list
    threads = []
    for i in range(max_threads):
        thread = NiahThreading()
        thread.start()
        threads.append(thread)

    # Fill the queue
    lock.acquire() #acquire the lock on thread to send data from the queue
    for host in hosts:
        task_queue.put(host)
        print 'Sent host to thread'

    lock.release() #release the lock

    # Wait for queue to empty
    while not task_queue.empty():
        pass

    # Notify threads it's time to exit
    exit_flag = 1

    # Tell the thread to exit and wait for all threads to complete
    for t in threads:
        t.join()

class NiahThreading(Thread):

    def __init__(self):
        Thread.__init__(self)

    def run(self):
        global lock, task_queue, exit_flag
        while not exit_flag:
            lock.acquire() #lock child thread and wait to receive data from parent thread
            if not task_queue.empty():
                ip = task_queue.get()
                lock.release()
                print 'Recieved host in Thread %s'%(ip)
            else:
                lock.release()


if __name__ == '__main__':
    #Set max number of threads
    if thread == True:
        start_threading(hosts=[1,2,3,4],max_threads=50)
