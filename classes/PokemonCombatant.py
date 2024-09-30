from classes.BaseStats import BaseStats
from classes.Move import Move
from classes.Pokemon import Pokemon
from classes.Enums import Stat
import random

def get_stage(stage):
    sign = lambda x: 1 if x > 0 else -1
    use_stage = stage if abs(stage) <= 6 else sign(stage) * 6
    return use_stage

class PokemonCombatant(Pokemon):
    def __init__(self, pokemon: Pokemon, stats, moves, combatant_id = 0):
        super().__init__(pokemon)

        self.id = combatant_id
        self.pokemon_id = pokemon.id
        self.moves = moves
        self.is_player = False

        self.types = [pokemon.type1, pokemon.type2]
        self.types.remove(None)

        if isinstance(stats, BaseStats):
            get_random_stat = lambda low, high : StatData(random.randint(low, high))
            self.stats = {
                Stat.ATTACK: get_random_stat(stats.attack_min,stats.attack_max),
                Stat.DEFENSE: get_random_stat(stats.defense_min,stats.defense_max),
                Stat.SP_ATTACK: get_random_stat(stats.sp_attack_min,stats.sp_attack_max),
                Stat.SP_DEFENSE: get_random_stat(stats.sp_defense_min,stats.sp_defense_max),
                Stat.SPEED: get_random_stat(stats.speed_min,stats.speed_max)
            }
            self.hp_max = get_random_stat(stats.hp_min, stats.hp_max).base_stat
            self.hp_current = self.hp_max
        else:
            self.stats = stats

    def modify_stage(self, move: Move):
        stat_data = self.stats[move.stat]
        stat_data.stage += move.stage_effect
        stat_data.stage = get_stage(stat_data.stage)

    def to_json(self):
        self.moves = [x.__dict__ for x in self.moves]
        self.stats = {k: v for d in [{x.value:y.__dict__} for x,y in self.stats.items()] for k, v in d.items()}
        return self.__dict__

    def types(self) -> set:
        return self.types

    def get_current_stat(self, stat: Stat):
        stat_data = self.stats[stat]
        use_stage = get_stage(stat_data.stage)
        return stat_data.base_stat * (1 + (.5 * use_stage))

class StatData:
    def __init__(self, base_stat, stage = 0):
        self.base_stat = base_stat
        self.stage = stage