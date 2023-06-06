from flask import Flask, render_template
from flask_cors import CORS, cross_origin
from flask_sock import Sock
from threading import Condition, Thread, Timer
import json
import uuid

############################################################################################
## VARIABLES, CONSTANTS & PARAMETERS
############################################################################################

# Cria uma instância para o Web Socket
app = Flask(__name__)
cors = CORS(app)
sock = Sock(app)

# Apenas um thread por vez pode adquirir o semáforo e
#  acessar o recurso compartilhado.
condition = Condition()

clients = []

# Tempo de turno de 3 segundos para o jogo
turn_time = 3
time = turn_time

# Dicionário de ações
actionDict = {
  'defense': 0,
  'load': 1,
  'attack': 2,
}

# Dicionários de informações sobre fraquezas entre pokemons
super_effective = {
  'grass': 'water',
  'water': 'fire',
  'fire': 'grass',
}

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


############################################################################################
## FUNCTIONS
############################################################################################

def strfy(s):
  """Converte um objeto python para uma string em formato JSON, para ser utilizada
     na rede"""
  return str(s).replace('\'', '\"').replace('None', 'null')


def clearUnusedConn(ws):
  """Remove todos os elementos da lista de clientes que não possuem mais uma conexão WebSocket
     ativa e não são a mesma conexão WebSocket que ws. Isso garante que a lista de clientes contenha
     apenas conexões WebSocket ativas."""
  global clients, pokemons
  clients = [c for c in clients if ((c['ws'].connected) or (c['ws'] == ws))]


def removeConn(ws):
  """Remove quaisquer elementos da lista de clientes que tenham a mesma conexão WebSocket que ws.
     Isso garante que a lista de clientes não inclua uma conexão WebSocket que foi fechada ou encerrada."""
  global clients, pokemons
  clients = [c for c in clients if (c['ws'] != ws)]


def broadcast(data):
  """Transmite os mesmos dados para todos os clientes conectados."""
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
    # usada para transmitir ou exibir informações sobre os threads num formato mais legível.
    'threads': list(map(lambda x: x.name, c['threads'])),
  }
  return player


def sendCurrentPlayerState(ws, c):
  msg = strfy({
    'action': 'player',
    'content': mapPlayer(c)
  })
  ws.send(msg)


def sendPlayersState(ws=None):
  global clients, pokemons
  msg = strfy({
    'action': 'all-players',
    'content': [mapPlayer(c) for c in clients]
  })
  if (ws == None):
    broadcast(msg)
  else:
    ws.send(msg)


def turn():
  sendTurn()
  t = Timer(1, turn)
  t.daemon = True
  t.start()


def sendTurn():
  global time, turn_time
  msg = strfy({
    'action': 'turn',
    'content': {'time': time},
  })
  if (time <= 0):
    time = turn_time
    calcTurn()
  time = time - 1
  broadcast(msg)


def calcTurn():
  """Pega as threads dos jogadores e os executa na ordem da ação que eles representam."""
  global clients, actionDict
  threadsToRun = []
  for c in clients:
    c['isDefending'] = False
    if (len(c['threads']) > 0):
      threadsToRun.append(c['threads'].pop(0))
  actionNames = list(map(lambda x: actionDict[x.name], threadsToRun))
  actionLives = list(map(lambda x: x['life'], clients))

  # As threads são classificados com base nas ações que representam e, em seguida, executados nessa ordem.

  # Primeiro são executadas as threads dos jogadores que entrarão no modo de defesa, depois dos jogadores que
  # recarregarão energia, e por fim, os jogadores que atacarão.

  # Em caso de empate, é feito primeiramente as ações nos jogadores com com menor vida restante.
  actions = [(actionNames[i], actionLives[i], threadsToRun[i]) for i in range(0, len(actionNames))]
  actions = sorted(actions, key=lambda x: (x[0], x[1]))
  sortedThreads = [x[2] for x in actions]

  # Antes de executar as threads, a função sendPlayersState() é chamada para atualizar os estados dos
  # players no lado do cliente.
  sendPlayersState()

  # Inicia as threads na ordem especificada
  for st in sortedThreads:
    st.start()


def attack(client):
  """Ataca todos os jogador na rede"""
  global condition, clients, super_effective

  # Caso o pokemon do cliente já tenha morrido, ou não tenha energia, não faça nada
  if (client['life'] <= 0): return
  if (client['energy'] <= 0): return

  # controla o acesso dos recursos compartilhado de maneira thread-safe, apenas
  # um cliente por vez pode acessar e alterar os dados globais da aplicação
  condition.acquire()

  # remove 1 de stamina do pokemon
  client['energy'] = client['energy'] - 1

  # Busca o tipo do jogador e o tipo na qual ele é super efetivo
  player_type = [p for p in pokemons if p['name'] == client['pokemonName']][0]['type']
  weak_type = super_effective[player_type]
  for c in clients:
    # Busca o tipo oponente e decide se ele é fraco quanto ao tipo do jogador
    opponent_type = [p for p in pokemons if p['name'] == c['pokemonName']][0]['type']
    opponent_weak = (opponent_type == weak_type)
    if (c != client):
      force = 10

      # Se o oponente for fraco quanto ao seu tipo, e ele estiver defendendo,
      # o oponente recebe +5% de vida
      if (opponent_weak and c['isDefending']):
        force = force * -0.5

      # Caso o oponente seja fraco ao seu tipo de golpe e não esteja defendendo, recebe 15% de dano
      elif (opponent_weak):
        force = force * 1.5

      # Caso o oponente não seja fraco ao seu tipo de ataque, recebe 1% de dano
      elif (c['isDefending']):
        force = force * 0.1

      # Aplica o dano ou cura ao oponente
      c['life'] = min(max(c['life'] - force, 0), 100)
  sendPlayersState()
  condition.release()


def defense(client):
  """Coloca o pokemon do jogador em modo de defesa"""
  global condition
  if (client['life'] <= 0): return

  # controla o acesso dos recursos compartilhado de maneira thread-safe, apenas
  # um cliente por vez pode acessar e alterar os dados globais da aplicação
  condition.acquire()

  client['isDefending'] = True
  sendPlayersState()
  condition.release()
  return


def load(client):
  """Adiciona +1 de stamina"""
  # controla o acesso dos recursos compartilhado de maneira thread-safe, apenas
  # um cliente por vez pode acessar e alterar os dados globais da aplicação
  condition.acquire()

  if (client['life'] <= 0): return
  client['energy'] = client['energy'] + 1
  sendPlayersState()
  condition.release()
  return


def saveThread(client, target, name):
  """Cria uma nova thread para um jogador realizar alguma ação, como atacar ou defender."""
  thrd = Thread(target=target, args=(client,), name=name)
  thrd.daemon = True
  client['threads'].append(thrd)
  sendPlayersState()


def doAction(ws, action, content):
  """Lida com diferentes ações que podem ser executadas por um cliente no jogo."""
  global clients, pokemons

  # Procura o cliente na lista de clientes com base no objeto WebSocket. Se o
  # cliente não for encontrado, a função retorna.
  client = None
  for c in clients:
    if (c['ws'] == ws):
      client = c
      break
  if (client == None):
    return

  if (action == 'select-pokemon'):
    # Procura um Pokémon com o nome indicado na lista de Pokémons.
    # Se um Pokémon for encontrado e o cliente ainda não tiver selecionado um Pokémon, o pokemonName do
    # cliente será definido como o nome do Pokémon selecionado,
    p = [p for p in pokemons if p['name'] == content]
    if (len(p) > 0 and client['pokemonName'] == None):
      p = p[0]
      client['pokemonName'] = p['name']
      sendPlayersState()
    return

  # Se a ação for "attack", "defense" ou "load", um novo thread é criado usando a função apropriada
  # e o thread é adicionado aos threads do cliente list usando a função saveThread().
  # A função saveThread() também chama sendPlayersState() para atualizar o estado de todos os clientes.
  elif (action == 'attack'):
    saveThread(client, attack, action)
    return
  elif (action == 'defense'):
    saveThread(client, defense, action)
    return
  elif (action == 'load'):
    saveThread(client, load, action)
    return


############################################################################################
## API ROUTES
############################################################################################

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
  return {'counter': counter}


@sock.route('/echo')
def echo(ws):
  global clients, pokemons

  # Cria um novo objeto player com um ID exclusivo, inicializa seus atributos e o adiciona à lista de clientes.
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

  # envia o estado atual do jogador para o jogador recém-conectado e envia o estado atualizado de todos os jogadores
  # para todos os clientes conectados.
  sendCurrentPlayerState(ws, newPlayer)
  sendPlayersState(ws)

  # Entra em um loop para receber e processar mensagens WebSocket recebidas.
  while True:
    try:
      # Espera que cada mensagem contenha uma ação e um campo de conteúdo no formato JSON.
      data = json.loads(ws.receive())
      action = data['action']
      content = data['content']

      # chama a função clearUnusedConn para remover qualquer cliente desconectado da lista
      clearUnusedConn(ws)

      # chama a função doAction para executar a ação apropriada com base na mensagem recebida.
      doAction(ws, action, content)
    except Exception as e:
      # Se ocorrer uma exceção durante o processamento de uma mensagem, o erro é impresso e o cliente
      # é removido da lista de clientes conectados caso não esteja mais conectado ao WebSocket.
      print('an error occured')
      print(e)
      if (not ws.connected):
        removeConn(ws)
        sendPlayersState()
        break


############################################################################################
## START TURN CLOCK
############################################################################################

turn()
