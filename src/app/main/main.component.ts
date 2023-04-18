import { HttpClient } from '@angular/common/http';
import { Component, OnInit } from '@angular/core';
import { first } from 'rxjs';

@Component({
  selector: 'main',
  templateUrl: './main.component.html',
  styleUrls: ['./main.component.scss']
})
export class MainComponent implements OnInit {

  title = 'pokemon';
  baseUrl = 'http://localhost:5000';
  baseWsUrl = 'ws://localhost:5000';
  pokemonList!: any;
  pokemonMap!: any;

  player: any;
  opponents: any;
  selectedPokemon: any;

  playing = false;

  ws!: WebSocket;

  constructor(private http: HttpClient) {

    this.ws = new WebSocket(`${this.baseWsUrl}/echo`);
    this.ws.addEventListener('message', ev => {
      const { action, content } = JSON.parse(ev.data);
      switch (action) {
        case 'player':
          this.player = content;
          break;
        case 'all-players':
          this.player = content.find((k: any) => k.playerId === this.player.playerId);
          this.opponents = content.filter((k: any) => k.playerId !== this.player.playerId);
          break;
        case 'turn':
          break;
        default: break;
      }
      this.playing = this.player?.pokemonName && this.opponents.length && this.opponents.every((k: any) => !!k.pokemonName) > 0;
    });
  }

  ngOnInit(): void {
    this.http.get(`${this.baseUrl}/pokemons`).pipe(first()).subscribe((pl: any) => {
      this.pokemonMap = {};
      pl.forEach((k: any) => this.pokemonMap[k.name] = k);
      this.pokemonList = pl;
    })
  }

  select(pokemon: any) {
    if(this.player?.pokemonName) return;
    const msg = {
      action: 'select-pokemon',
      content: pokemon.name,
    };
    this.ws.send(JSON.stringify(msg));
  }

  attack() {
    const msg = {
      action: 'attack',
      content: '',
    };
    this.ws.send(JSON.stringify(msg));
  }
}
