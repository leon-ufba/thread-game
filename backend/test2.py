from threading import Semaphore, Thread, Timer


clients = [['defense','2','3'], ['attack','5','6'], ['load','8','9']]

def display(name):
  print(name)
  return

def nToThread(n):
  return Thread(target = display , args = ('Thread-'+n,), name=n)

clients = [list(map(nToThread, c)) for c in clients]

actionDict = {
  'defense':  0,
  'load':     1,
  'attack':   2,
}

threadsToRun = []
for c in clients:
  threadsToRun.append(c.pop(0))
print(clients)
print(threadsToRun)
names = list(map(lambda x: actionDict[x.name], threadsToRun))
lifes = [15, 5, 30]
tuples = [(names[i], lifes[i], threadsToRun[i]) for i in range(0, len(names))]

print(names)
print(tuples)
tuples = sorted(tuples, key=lambda x:(x[0], x[1]))
print(tuples)
print([x[2] for x in tuples])