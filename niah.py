from threading import Thread, Lock
from Queue import Queue
import argparse

thread = True
exit_flag = 0
lock = Lock()
task_queue = Queue()

def threading(**kwargs):
    global lock, task_queue, exit_flag
    hosts = kwargs['hosts']
    max_threads = kwargs['max_threads']
    if len(hosts) < max_threads:
        max_threads = len(hosts)

    #set thread list
    threads = []
    for i in range(max_threads):
        thread = Thread(target=worker,args=kwargs['activity'])
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

def worker(activity):
    global lock, task_queue, exit_flag
    while not exit_flag:
        lock.acquire() #lock child thread and wait to receive data from parent thread
        if not task_queue.empty():
            ip = task_queue.get() # Get the host from the queue
            lock.release()
            run(ip,activity)
        else:
            lock.release()

def run(host,activity):
    execfile(activity)

if __name__ == '__main__':
    #Set up system arguments
    parser = argparse.ArgumentParser()

    arguments = {
                    '-d':{
                            'choices': range(1,5),
                            'dest':'debug',
                            'type': int,
                            'help': 'set debug level 1=Critical, 2=Warning, 3=Info, 4=Debug',
                            'default': 0
                        },
                    '--thread':{
                            'action':'store_true',
                            'dest':'thread',
                            'help':'use threading',
                            'default': False
                    },
                    '--hosts':{
                            'action':'append',
                            'dest':'hosts',
                            'nargs':'*',
                            'help':'specify hosts'
                    },
                    '-f':{
                            'dest': 'hosts',
                            'help':'specify hosts from file',
                            'type': argparse.FileType('r')
                    },
                    '-a':{
                            'dest':'activity',
                            'help':'sepcify which activity to run (from file that contains python)',
                            'type': str
                    }
                }

    for k,v in arguments.iteritems():
        parser.add_argument(k,**v)

    arg = parser.parse_args()

    thread = arg.thread

    if type(arg_vals.hosts) == file:
        hosts = arg.hosts.read().splitlines()
    else:
        hosts = arg.hosts

    activity = arg.activity

    #Set max number of threads
    if thread == True:
        threading(hosts=hosts,max_threads=50,activity=activity)
    else:
        for host in hosts:
            run(host, activity)
