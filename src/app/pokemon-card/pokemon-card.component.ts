import { Component, Input } from '@angular/core';

@Component({
  selector: 'pokemon-card',
  templateUrl: './pokemon-card.component.html',
  styleUrls: ['./pokemon-card.component.scss']
})
export class PokemonCardComponent {
  @Input() pokemon!: any;
  @Input() life!: number;
  @Input() energy: number = 0;
  @Input() isDefending: number = 0;
  @Input() disabled: boolean = false;
  @Input() selected: boolean = false;
  @Input() hover: boolean = true;

  lifeColor(life: number) {
    const green = (life >= 50) ? 255 : Math.round(255 * (life)/(50 - 0));
    const red = (life <= 50) ? 255 : Math.round(255 * (100 - life)/(100 - 50));
    return `rgb(${red},${green},0)`
  }
}
