import copy

from src.classes.PokemonCombatant import PokemonCombatant
from src.repositories.redis_connect import store_data_in_redis
from src.utils.utils import jsonify_dict, get_player_or_enemy_id


class GameComplete:
    def __init__(self, id, pokemon):
        self.id = int(id)
        self.pokemon = {get_player_or_enemy_id(x): x for x
                        in [p if isinstance(p, PokemonCombatant)
                            else PokemonCombatant(**p)
                            for p in (pokemon if isinstance(pokemon, list) else pokemon.values())]}
        store_data_in_redis(copy.deepcopy(self))

    def to_json(self):
        self.pokemon = jsonify_dict(self.pokemon)
        return self.__dict__