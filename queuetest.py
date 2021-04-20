from queue import Queue
from threading import Thread
import time


def do_stuff(q):
	print('running')
	while True:
		print(q.get())
		print(str(list(q.queue))+' add to queue: ', end="")
		time.sleep(3)
		q.task_done()

q = Queue(maxsize=0)
# num_threads = 10
worker = Thread(target=do_stuff, args=(q,))
worker.setDaemon(True)
worker.start()
# for i in range(num_threads):
#   worker = Thread(target=do_stuff, args=(q,))
#   worker.setDaemon(True)
#   worker.start()
usr = ""
while usr != "exit":
	usr = input(str(list(q.queue))+' add to queue: ')
	q.put(usr)
print('exiting...')
q.join()