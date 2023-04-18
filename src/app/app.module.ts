import { NgModule } from '@angular/core';
import { BrowserModule } from '@angular/platform-browser';
import { MainComponent } from './main/main.component';
import { HttpClientModule } from '@angular/common/http';
import { PokemonCardComponent } from './pokemon-card/pokemon-card.component';


@NgModule({
  imports: [
    BrowserModule,
    HttpClientModule,
  ],
  declarations: [
    MainComponent,
    PokemonCardComponent,
  ],
  providers: [],
  bootstrap: [MainComponent]
})
export class AppModule { }
