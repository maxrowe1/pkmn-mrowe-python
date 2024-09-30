import random

from db_connect import Pokemon, get_pokemon_stats, get_pokemon_moves


class PokemonCombatant(Pokemon):
    def __init__(self, pokemon, stats, moves):
        super().__init__(pokemon.id, pokemon.name, pokemon.type1, pokemon.type2)
        get_random_stat = lambda low, high : random.randint(low, high)
        self.attack = get_random_stat(stats.attack_min,stats.attack_max)
        self.defense = get_random_stat(stats.defense_min,stats.defense_max)
        self.sp_attack = get_random_stat(stats.sp_attack_min,stats.sp_attack_max)
        self.sp_defense = get_random_stat(stats.sp_defense_min,stats.sp_defense_max)
        self.speed = get_random_stat(stats.speed_min,stats.speed_max)
        self.hp = get_random_stat(stats.hp_min,stats.hp_max)
        self.moves = moves

    def to_json(self):
        self.moves = [x.__dict__ for x in self.moves]
        return self.__dict__

def generate_combatant(pokemon_id):
    pokemon_stats_map = get_pokemon_stats(pokemon_id)[pokemon_id]
    pokemon = pokemon_stats_map["pokemon"]
    stats = pokemon_stats_map["stats"]
    moves = get_pokemon_moves(pokemon_id)[pokemon_id]
    return PokemonCombatant(pokemon, stats, moves)

def generate_combatants(combatant_id_dict):
    pokemon_ids = list(combatant_id_dict.values())
    pokemon_stats_map = get_pokemon_stats(*pokemon_ids)
    moves_map = get_pokemon_moves(*pokemon_ids)
    combatants = {}
    for combatant_id, pokemon_id in combatant_id_dict.items():
        pokemon_stats = pokemon_stats_map[pokemon_id]
        pokemon = pokemon_stats["pokemon"]
        stats = pokemon_stats["stats"]
        moves = moves_map[pokemon_id]
        combatants[combatant_id] = PokemonCombatant(pokemon, stats, moves)
    return combatants
