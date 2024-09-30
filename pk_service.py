import copy
import random

from classes.Enums import Category, Stat
from classes.Move import Move

from classes.PokemonCombatant import PokemonCombatant
from db_connect import get_pokemon_stats, get_pokemon_moves, create_combatants, save_game


def generate_combatant(pokemon_id, create_in_db = False):
    pokemon_stats_map = get_pokemon_stats(pokemon_id)[pokemon_id]
    pokemon = pokemon_stats_map["pokemon"]
    stats = pokemon_stats_map["stats"]
    moves = get_pokemon_moves(pokemon_id)[pokemon_id]
    combatant = PokemonCombatant(pokemon, stats, moves)
    if create_in_db:
        create_combatants(combatant)
    return combatant

def generate_combatants(combatant_id_dict):
    combatants = {}
    for combatant_id, pokemon_id in combatant_id_dict.items():
        combatants[combatant_id] = generate_combatant(pokemon_id, False)
        combatants[combatant_id].is_player = combatant_id == 0
    combatants = create_combatants(*tuple(combatants.values()))
    combatants = {0 if x.is_player else 1: x for x in combatants}
    save_game(combatants[0].id, combatants[1].id)
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
            stat = phy if is_physical else spc
            stat_data = pokemon.stats[stat]
            return stat_data.base_stat if critical_mod > 1 else pokemon.get_current_stat(stat)

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
    # TODO: Save changes to db

