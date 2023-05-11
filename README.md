# Pokemon
#### Integrantes da Equipe
- Daniel Carneiro
- Fredson Menezes Sumi Barreto
- Leon Santos
- Yago Martins


## Instruções de instalação do projeto
### Instalando python
Primeiramente, deve-ser ter instalado uma vesão do python3, superior a 3.7.0 (Foi testado utilizando python 3.10.11)

### Instalando bibliotecas
Entre na pasta back end
```cd backend```

Ative um ambiente, se for desejado
```
python -m venv venv
venv\Scripts\activate
```

Instale as bibliotecas necessárias pelo projeto, utilizando a biblioteca pip
```
python -m pip install -r requirements.txt
```

### Iniciando o servidor e o jogo
Para iniciar o servidor, simplesmente entre na pasta backend, e digite o comando
```flask --app main run```

Agora, para jogar, abra seu navegador, e entre o url `localhost:5000`.

Para simular o modo multijogador, simplesmente abra multiplas abas com esse link, cada aba nova será um jogador novo

