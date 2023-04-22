
# importing the modules
from random import random
from threading import *
import time



def strfy(s):
  return str(s).replace('\'', '\"').replace('None', 'null')

turn_time = 5
curr_time = turn_time
def turn():
  sendTurn()
  thrd = Timer(1, turn)
  thrd.setDaemon(True)
  thrd.start()

def sendTurn():
  global curr_time, turn_time
  msg = strfy({
    'action': 'turn',
    'content': { 'curr_time': curr_time },
  })
  curr_time = curr_time - 1
  if(curr_time <= 0): curr_time = turn_time
  print(curr_time)
  # broadcast(msg)

print('start')
turn()
print('end')

time.sleep(5)
print('this is Main Thread') 


'''
# creating thread instance where count = 3
semaphore = Semaphore(1)

# creating instance
def display(name):
  r = random()
  print(semaphore._value, name, r)
  curr_time.sleep(r)
  semaphore.acquire()
  print()
  print(name)
  semaphore.release()

# print(semaphore._value)

thrds = []

# creating multiple thread
thrds.append(Thread(target = display , args = ('Thread-1',), name='A'))
thrds.append(Thread(target = display , args = ('Thread-2',), name='A'))
thrds.append(Thread(target = display , args = ('Thread-3',), name='C'))
thrds.append(Thread(target = display , args = ('Thread-4',), name='D'))
thrds.append(Thread(target = display , args = ('Thread-5',), name='E'))

print(list(map(lambda t: t.name, thrds)))

# calling the threads
for t in thrds:
  t.start()

# wait until thread 1 is completely executed
# t1.join()

'''