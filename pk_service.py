import copy
import random
from enum import Enum
from db_connect import Pokemon, get_pokemon_stats, get_pokemon_moves, Category, BaseStats, Move

class Stat(Enum):
    ATTACK = "ATTACK"
    DEFENSE = "DEFENSE"
    SP_ATTACK = "SP_ATTACK"
    SP_DEFENSE = "SP_DEFENSE"
    SPEED = "SPEED"

class StatData:
    def __init__(self, base_stat, stage = 0):
        self.base_stat = base_stat
        self.stage = stage

class PokemonData(Pokemon):
    def __init__(self, pokemon: Pokemon, stats: BaseStats, moves):
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

def get_current_stat(stat):
    use_stage = get_stage(stat.stage)
    return stat.base_stat * (1 + (.5 * use_stage))


def get_stage(stage):
    sign = lambda x: 1 if x > 0 else -1
    use_stage = stage if abs(stage) <= 6 else sign(stage) * 6
    return use_stage


class PokemonCombatant:
    def __init__(self, pokemon_data: PokemonData):
        types = {pokemon_data.type1, pokemon_data.type2}
        types.remove(None)

        self.hp_total = pokemon_data.hp
        self.hp_current = pokemon_data.hp
        self.types: set = types
        self.stats = {
            Stat.ATTACK: StatData(pokemon_data.attack),
            Stat.DEFENSE: StatData(pokemon_data.defense),
            Stat.SP_ATTACK: StatData(pokemon_data.sp_attack),
            Stat.SP_DEFENSE: StatData(pokemon_data.sp_defense),
            Stat.SPEED: StatData(pokemon_data.speed)
        }

    def modify_stage(self, move: Move):
        stat_data = self.stats[move.stat]
        stat_data.stage += move.stage_effect
        stat_data.stage = get_stage(stat_data.stage)

def generate_combatant(pokemon_id):
    pokemon_stats_map = get_pokemon_stats(pokemon_id)[pokemon_id]
    pokemon = pokemon_stats_map["pokemon"]
    stats = pokemon_stats_map["stats"]
    moves = get_pokemon_moves(pokemon_id)[pokemon_id]
    return PokemonData(pokemon, stats, moves)

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
        combatants[combatant_id] = PokemonData(pokemon, stats, moves)
    return combatants

def use_move_on_pokemon(move: Move, defender: PokemonCombatant, attacker: PokemonCombatant):
    if move.accuracy < 100:
        rand_accuracy = random.randint(0, 100)
        if rand_accuracy > move.accuracy:
            # Move missed; no changes
            return defender

    # Move hits
    if move.category != Category.STATUS:
        def get_critical():
            """
            Calculated based on Stat stage from attacker; TODO: simple for now; include stages
            :return:
            """
            return 2 if random.randint(1, 24) == 1 else 1

        def get_damage_random(penultimate_damage):
            """
            random is realized as a multiplication by a random uniformly distributed integer between 217 and 255 (inclusive),
            followed by an integer division by 255. If the calculated damage thus far is 1, random is always 1.
            :param penultimate_damage: Damage calculated up until this point
            :return: Final damage calculation
            """
            if penultimate_damage == 1:
                return 1
            return random.randint(217, 255) / 255

        def get_score(pokemon: PokemonCombatant, phy, spc):
            """
            Effective physical stat of the Pokémon if the used move is a physical move, or the effective Special stat
            of the Pokémon if the used move is a special move.
            For a critical hit, all modifiers are ignored, and the unmodified stat is used instead).
            :param pokemon: Attacker or Defender
            :param phy: Attack or Defense
            :param spc: Special Attack or Special Defense
            :return: Value of stat, with stage modifiers
            """
            is_physical = move.category == Category.PHYSICAL
            stat_data = pokemon.stats[phy if is_physical else spc]
            return stat_data.base_stat if critical_mod > 1 else get_current_stat(stat_data)

        defender2 = copy.deepcopy(defender)

        critical_mod = 1 if not move.can_crit else get_critical()

        attack = get_score(attacker, Stat.ATTACK, Stat.SP_ATTACK)
        defense = get_score(defender, Stat.DEFENSE, Stat.SP_DEFENSE)

        # Same type ability bonus (move type matches one of the attacker's two types)
        stab = 1.5 if move.type in attacker.types else 1

        type_bonus = 1 # TODO: Not very effective, super effective, product of both target types

        # Generation 1 damage calculation, as seen on Bulbapedia
        damage = (( (((2 * critical_mod) / 5 + 2) * move.power * (attack/defense)) / 50 ) + 2) * stab * type_bonus
        damage = damage * get_damage_random(damage)

        # HP = HP - damage (rounded down); HP minimum of 0
        hp_current = defender2.hp_current - damage // 1
        defender2.hp_current = 0 if hp_current < 0 else hp_current

        return defender2
    else:
        # Target is affected by stat changes
        target = copy.deepcopy(attacker if move.target_self else defender)
        target.modify_stage(move)
        return target

