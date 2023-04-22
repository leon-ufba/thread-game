from flask import Flask, render_template
from flask_cors import CORS, cross_origin
from flask_sock import Sock
from threading import Semaphore, Thread, Timer
import json
import uuid

app = Flask(__name__)
cors = CORS(app)
sock = Sock(app)

semaphore = Semaphore(1)

clients = []

# https://superfastpython.com/thread-semaphore/

pokemons = [
  {
    "name": "Bulbasaur",
    "image": "https://assets.pokemon.com/assets/cms2/img/pokedex/full/001.png",
    "type": "grass"
  },
  {
    "name": "Charmander",
    "image": "https://assets.pokemon.com/assets/cms2/img/pokedex/full/004.png",
    "type": "fire"
  },
  {
    "name": "Squirtle",
    "image": "https://assets.pokemon.com/assets/cms2/img/pokedex/full/007.png",
    "type": "water"
  },
]


def strfy(s):
  return str(s).replace('\'', '\"').replace('None', 'null')

def clearUnusedConn(ws):
  global clients, pokemons
  clients = [c for c in clients if((c['ws'].connected) or (c['ws'] == ws))]

def removeConn(ws):
  global clients, pokemons
  clients = [c for c in clients if(c['ws'] != ws)]

def broadcast(data):
  global clients, pokemons
  for c in clients:
    c['ws'].send(data)

def mapPlayer(c):
  player = {
    'playerId': c['playerId'],
    'pokemonName': c['pokemonName'],
    'life': c['life'],
    'energy': c['energy'],
    'isDefending': 1 if c['isDefending'] else 0,
    'threads': list(map(lambda x: x.name, c['threads'])),
  }
  return player

def sendCurrentPlayerState(ws, c):
  msg = strfy({
    'action': 'player',
    'content': mapPlayer(c)
  })
  ws.send(msg)

def sendPlayersState(ws = None):
  global clients, pokemons
  msg = strfy({
    'action': 'all-players',
    'content': [mapPlayer(c) for c in clients]
  })
  if(ws == None): broadcast(msg)
  else: ws.send(msg)

def turn():
  sendTurn()
  t = Timer(1, turn)
  t.setDaemon(True)
  t.start()

turn_time = 4
time = turn_time
def sendTurn():
  global time, turn_time
  msg = strfy({
    'action': 'turn',
    'content': { 'time': time },
  })
  if(time <= 0):
    time = turn_time
    calcTurn()
  time = time - 1
  broadcast(msg)

actionDict = {
  'defense':  0,
  'load':     1,
  'attack':   2,
}
def calcTurn():
  global clients, actionDict
  threadsToRun = []
  for c in clients:
    c['isDefending'] = False
    if(len(c['threads']) > 0):
      threadsToRun.append(c['threads'].pop(0))
  actionNames = list(map(lambda x: actionDict[x.name], threadsToRun))
  actionLives = list(map(lambda x: x['life'], clients))
  actions = [(actionNames[i], actionLives[i], threadsToRun[i]) for i in range(0, len(actionNames))]
  actions = sorted(actions, key=lambda x:(x[0], x[1]))
  sortedThreads = [x[2] for x in actions]
  sendPlayersState()
  for st in sortedThreads:
    st.start()


super_effective = {
  'grass': 'water',
  'water': 'fire' ,
  'fire' : 'grass',
}
def attack(client):
  global semaphore, clients, super_effective
  if(client['life']   <= 0): return
  if(client['energy'] <= 0): return
  semaphore.acquire()
  client['energy'] = client['energy'] - 1
  player_type = [p for p in pokemons if p['name'] == client['pokemonName']][0]['type']
  weak_type = super_effective[player_type]
  for c in clients:
    opponent_type = [p for p in pokemons if p['name'] == c['pokemonName']][0]['type']
    opponent_weak = (opponent_type == weak_type)
    if(c!= client):
      force = 10
      if(opponent_weak and c['isDefending']):
        force = force * -0.5
      elif(opponent_weak):
        force = force * 1.5
      elif(c['isDefending']):
        force = force * 0.1
      c['life'] = min(max(c['life'] - force, 0), 100)
  sendPlayersState()
  semaphore.release()

def defense(client):
  global semaphore
  if(client['life'] <= 0): return
  semaphore.acquire()
  client['isDefending'] = True
  sendPlayersState()
  semaphore.release()
  return

def load(client):
  semaphore.acquire()
  if(client['life'] <= 0): return
  client['energy'] = client['energy'] + 1
  sendPlayersState()
  semaphore.release()
  return

def saveThread(client, target, name):
  thrd = Thread(target=target, args=(client,), name=name)
  thrd.setDaemon(True)
  client['threads'].append(thrd)
  sendPlayersState()

def doAction(ws, action, content):
  global clients, pokemons
  client = None
  for c in clients:
    if(c['ws'] == ws):
      client = c
      break
  if(client == None):
    return
  if(action == 'select-pokemon'):
    p = [p for p in pokemons if p['name'] == content]
    if(len(p) > 0 and client['pokemonName'] == None):
      p = p[0]
      client['pokemonName'] = p['name']
      sendPlayersState()
    return
  elif(action == 'attack'):
    saveThread(client, attack, action)
    return
  elif(action == 'defense'):
    saveThread(client, defense, action)
    return
  elif(action == 'load'):
    saveThread(client, load, action)
    return


@app.get('/')
def get_value():
  return render_template('index.html')

@app.get('/pokemons')
def get_pokemons():
  return pokemons

@app.post('/attack')
def increase():
  global counter
  counter = counter + 1
  return { 'counter': counter }

@sock.route('/echo')
def echo(ws):
  global clients, pokemons
  newPlayer = {
    'ws': ws,
    'playerId': str(uuid.uuid4()),
    'pokemonName': None,
    'life': 100,
    'energy': 1,
    'isDefending': False,
    'threads': [],
  }
  clients.append(newPlayer)
  sendCurrentPlayerState(ws, newPlayer)
  sendPlayersState(ws)
  while True:
    try:
      data = json.loads(ws.receive())
      action = data['action']
      content = data['content']
      clearUnusedConn(ws)
      doAction(ws, action, content)
    except Exception as e:
      print('an error occured')
      print(e)
      if(not ws.connected):
        removeConn(ws)
        sendPlayersState()
        break

turn()