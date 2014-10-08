import threading, subprocess,shlex,time, Queue
from datetime import datetime

max_number_of_threads = 1 # Set the number of threads

process_timeout = 60*2 # Set the process timeout

taskQueue = Queue.Queue(10000000)
count = 0

def genTask(proto,ip): # Generate the command and file name
    cmd = ["scrapy runspider ../scrapySpider/MySpider.py -a db=./urls.db -a urls_num=1 -a start_url1=%s://%s"%(proto,ip), "out/%s.txt"%(ip)]
#    print cmd
    return cmd

class Executor(threading.Thread):  
    def __init__(self, lock, threadName):  
        super(Executor, self).__init__(name = threadName)
        self.lock = lock
     
    def run(self):  
        global taskQueue
        global count
        global process_timeout
        self.lock.acquire()
        count=count+1
        self.lock.release()
        while True:
            self.lock.acquire()
            if taskQueue.empty():
                self.lock.release()
                break
            r=taskQueue.get()
            print "\n\n------------------------------"
            print "%s << %s"%(self.name, r)
            print "[%d]"%(taskQueue.qsize())
            print "------------------------------\n\n"
            self.lock.release()
            [cmd, fn]=r
            fp=open(fn,"a")
            fp.write("-------- %s --------\n"%(datetime.now().isoformat("-")))
            fp.flush()
            p=subprocess.Popen(shlex.split(cmd), stdout = fp, shell = False)
            for i in range(0,process_timeout):
                time.sleep(1)
                if p.poll() != None:
                    break;
            if p.poll() == None:
                p.terminate()
            fp.close()
        print "%s done"%(self.name)
        self.lock.acquire()
        count=count-1
        self.lock.release()

if __name__ == '__main__':
    lock = threading.Lock()
    
    f = open('ip_list.txt', 'r')
    for line in f.readlines():
        line = line.strip()
        if not len(line) or line.startswith('#'):
            continue
        taskQueue.put(genTask("http",line))
        
    for i in range(0, max_number_of_threads):
        Executor(lock, "thread-" + str(i)).start()
    while True:
        time.sleep(1)
        if taskQueue.empty():
            if count==0:
                break;
    print "All done"
