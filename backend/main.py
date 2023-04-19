from flask import Flask, render_template
from flask_cors import CORS, cross_origin
from flask_sock import Sock
from threading import Semaphore
import json
import uuid

app = Flask(__name__)
cors = CORS(app)
sock = Sock(app)

semaphore = Semaphore(100)

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

def sendCurrentPlayerState(ws, c):
  msg = strfy({
    'action': 'player',
    'content': {
      'playerId': c['playerId'],
      'pokemonName': c['pokemonName'],
      'life': c['life'],
    }
  })
  ws.send(msg)

def sendPlayersState(ws = None):
  global clients, pokemons
  msg = strfy({
    'action': 'all-players',
    'content': [{
      'playerId': c['playerId'],
      'pokemonName': c['pokemonName'],
      'life': c['life'],
    } for c in clients]
  })
  if(ws == None): broadcast(msg)
  else: ws.send(msg)

def sendTurn():
  global clients, pokemons
  msg = strfy({
    'action': 'turn',
    'content': {
      'playerId': c['playerId'],
      'time': 10,
    }
  })
  broadcast(msg)

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
    if(client['life'] <= 0): return
    player_type = [p for p in pokemons if p['name'] == client['pokemonName']][0]['type']
    for c in clients:
      opponent_type = [p for p in pokemons if p['name'] == c['pokemonName']][0]['type']
      if(c!= client):
        grass_force = player_type == 'grass' and opponent_type == 'water'
        water_force = player_type == 'water' and opponent_type == 'fire'
        fire_force  = player_type == 'fire'  and opponent_type == 'grass'
        force = 15 if (grass_force or water_force or fire_force) else 10
        c['life'] = max(c['life'] - force, 0)
    sendPlayersState()
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

