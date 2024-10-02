import copy
import random

from classes.Enums import Category, Stat
from classes.GameComplete import GameComplete
from classes.Move import Move

from classes.PokemonCombatant import PokemonCombatant
from db_connect import get_pokemon_stats, get_pokemon_moves, create_combatants, get_game_data, get_combatant_data, \
    save_game
from redis_connect import get_data_in_redis
from utils import get_player_or_enemy_id


def generate_combatant(player_or_enemy_id, pokemon_id):
    pokemon_stats_map = get_pokemon_stats(pokemon_id)[pokemon_id]
    pokemon = pokemon_stats_map["pokemon"]
    stats = pokemon_stats_map["stats"]
    moves = get_pokemon_moves(pokemon_id)[pokemon_id]
    combatant = PokemonCombatant(pokemon, stats, moves)
    combatant.is_player = player_or_enemy_id == 0
    combatant = create_combatants(combatant)[0]
    return combatant

def generate_combatants(combatant_id_dict):
    combatants = {}
    for player_or_enemy_id, pokemon_id in combatant_id_dict.items():
        combatants[player_or_enemy_id] = generate_combatant(player_or_enemy_id, pokemon_id)
    combatants = {get_player_or_enemy_id(x): x for x in combatants.values()}
    return combatants

def get_game(game_id):
    game = get_data_in_redis(game_id)
    if game is not None:
        combatants = game["pokemon"]
    else:
        game = get_game_data(game_id)
        combatants = get_combatant_data(game.player_combatant_id, game.enemy_combatant_id)
    return GameComplete(game_id, combatants)

def new_game(combatant_id_dict):
    combatants_map = generate_combatants(combatant_id_dict)
    game = save_game(combatants_map[0].id, combatants_map[1].id)
    return GameComplete(game.id, combatants_map)

def use_move_on_pokemon(move: Move, target: PokemonCombatant, attacker: PokemonCombatant):
    if move.accuracy < 100:
        rand_accuracy = random.randint(0, 100)
        if rand_accuracy > move.accuracy:
            # Move missed; no changes
            return target

    # Move hits
    if move.category != Category.STATUS:
        def get_critical():
            """
            Gen I math
            Gen VII+ probability
            Calculated based on Stat stage from attacker; TODO: simple for now; include stages
            :return:
            """
            return 2 if random.randint(1, 24) == 1 else 1

        def get_damage_random(penultimate_damage):
            """
            Gen I description
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
            Gen I description
            Effective physical stat of the Pokémon if the used move is a physical move, or the effective Special stat
            of the Pokémon if the used move is a special move.
            For a critical hit, all modifiers are ignored, and the unmodified stat is used instead.
            :param pokemon: Attacker or Defender
            :param phy: Attack or Defense
            :param spc: Special Attack or Special Defense
            :return: Value of stat, with stage modifiers
            """
            is_physical = move.category == Category.PHYSICAL
            stat = phy if is_physical else spc
            stat_data = pokemon.stats[stat]
            return stat_data.base_stat if critical_mod > 1 else pokemon.get_current_stat(stat)

        updated_target = copy.deepcopy(target)

        # Damage is increased based on randomized critical hit modifier
        critical_mod = 1 if not move.can_crit else get_critical()

        # The effective (Special)Attack stat of the attacking Pokémon
        attack = get_score(attacker, Stat.ATTACK, Stat.SP_ATTACK)
        # The effective (Special)Defense stat of the updated_target
        defense = get_score(target, Stat.DEFENSE, Stat.SP_DEFENSE)

        # Same type ability bonus (move type matches one of the attacker's two types)
        stab = 1.5 if move.type in attacker.types else 1

        type_bonus = 1 # TODO: Not very effective, super effective, product of both updated_target types

        # Gen I damage calculation, as seen on Bulbapedia
        damage = (( (((2 * critical_mod) / 5 + 2) * move.power * (attack/defense)) / 50 ) + 2) * stab * type_bonus
        damage = damage * get_damage_random(damage)

        # HP = HP - damage (rounded down); HP minimum of 0
        hp_current = updated_target.hp_current - damage // 1
        updated_target.hp_current = 0 if hp_current < 0 else hp_current

        return updated_target
    else:
        # Target is affected by stat changes
        updated_target = copy.deepcopy(attacker if move.target_self else target)
        updated_target.modify_stage(move)
        return updated_target
    # TODO: Save changes to db; combatants, combatant_moves (pp), combatant_stats

