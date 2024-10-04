from src.classes.BaseStats import BaseStats
from src.classes.Move import Move
from src.classes.Pokemon import Pokemon
from src.classes.Enums import Stat
import random

from src.utils.utils import jsonify_dict


def get_stage(stage):
    sign = lambda x: 1 if x > 0 else -1
    use_stage = stage if abs(stage) <= 6 else sign(stage) * 6
    return use_stage

class PokemonCombatant:
    def __init__(self, pokemon, stats, moves, **kwargs):
        self.id = kwargs["id"] if len(kwargs) > 1 else 0
        self.pokemon = pokemon if isinstance(pokemon, Pokemon) else Pokemon(**pokemon)
        self.moves = [x if isinstance(x, Move) else Move(**x) for x in moves]
        self.is_player = False

        self.types = [self.pokemon.type1, self.pokemon.type2]
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
            self.hp_max = kwargs["hp_max"]
            self.hp_current = kwargs["hp_current"]
            self.is_player = kwargs["is_player"]

    def modify_stage(self, move: Move):
        stat_data = self.stats[move.stat]
        stat_data.stage += move.stage_effect
        stat_data.stage = get_stage(stat_data.stage)

    def to_json(self):
        self.pokemon = self.pokemon.__dict__
        self.moves = [x.__dict__ for x in self.moves]
        self.stats = jsonify_dict(self.stats)
        return self.__dict__

    def get_current_stat(self, stat: Stat):
        stat_data = self.stats[stat]
        use_stage = get_stage(stat_data.stage)
        return stat_data.base_stat * (1 + (.5 * use_stage))

class StatData:
    def __init__(self, base_stat, stage = 0):
        self.base_stat = base_stat
        self.stage = stage