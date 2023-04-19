
# importing the modules
from random import random
from threading import *
import time

# creating thread instance where count = 3
semaphore = Semaphore(1)

# creating instance
def display(name):
  print(semaphore._value)
  time.sleep(random())
  semaphore.acquire()
  print('')
  print(name)
  print(semaphore._value)
  semaphore.release()
  print(semaphore._value)

# print(semaphore._value)

# creating multiple thread 
t1 = Thread(target = display , args = ('Thread-1',))
t2 = Thread(target = display , args = ('Thread-2',))
t3 = Thread(target = display , args = ('Thread-3',))
t4 = Thread(target = display , args = ('Thread-4',))
t5 = Thread(target = display , args = ('Thread-5',))

# calling the threads 
t1.start()
t2.start()
t3.start()
t4.start()
t5.start()

# wait until thread 1 is completely executed
t1.join()