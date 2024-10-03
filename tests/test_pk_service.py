import pytest

from classes.Enums import Type, Category
from db_connect import Pokemon, Move, BaseStats, delete_combatants, create_combatants, save_combatant_stats, \
    get_combatant_stats
from pk_service import generate_combatant, generate_combatants, \
    use_move_on_pokemon, Stat, PokemonCombatant, new_game, get_last_game


class TestClass:
    def __init__(self, name):
        self.name = name

@pytest.fixture
def setup_combatants():
    pokemon1 = Pokemon(1, 'BeepBop', Type.NORMAL, None)
    pokemon2 = Pokemon(2, 'Zorp', Type.NORMAL, None)
    stats1 = BaseStats({
        "hp_min": 200,
        "hp_max": 200,
        "attack_min": 50,
        "attack_max": 50,
        "defense_min": 60,
        "defense_max": 60,
        "sp_attack_min": 30,
        "sp_attack_max": 30,
        "sp_defense_min": 100,
        "sp_defense_max": 100,
        "speed_min": 20,
        "speed_max": 20
    })
    stats2 = BaseStats({
        "hp_min": 50,
        "hp_max": 50,
        "attack_min": 20,
        "attack_max": 20,
        "defense_min": 25,
        "defense_max": 25,
        "sp_attack_min": 5,
        "sp_attack_max": 5,
        "sp_defense_min": 60,
        "sp_defense_max": 60,
        "speed_min": 20,
        "speed_max": 20
    })

    attacker = PokemonCombatant(pokemon1, stats1, [])
    defender = PokemonCombatant(pokemon2, stats2, [])

    create_combatants(attacker, defender)

    yield attacker, defender

    delete_combatants(attacker.id, defender.id)

def test_generate_combatant():
    result1 = generate_combatant(0, 1)
    assert result1.pokemon.id == 1
    assert result1.pokemon.name == 'Charmander'
    assert 98 <= result1.stats[Stat.ATTACK].base_stat <= 223
    assert result1.hp_max == result1.hp_max
    assert len(result1.moves) == 2
    assert result1.is_player

    # No two generations are the same (possible but unlikely)
    result2 = generate_combatant(0, 2)
    assert result1 != result2
    assert (result1.stats[Stat.ATTACK] != result2.stats[Stat.ATTACK] or
            result1.stats[Stat.DEFENSE] != result2.stats[Stat.DEFENSE])


def test_generate_combatants():
    results = generate_combatants({0: 1, 1: 2})
    assert results[0].pokemon.name == 'Charmander'
    assert results[1].pokemon.name == 'Squirtle'
    assert len([move for move in results[0].moves if move.name == 'Scratch']) == 1
    assert len([move for move in results[0].moves if move.name == 'Tackle']) == 0
    assert len([move for move in results[1].moves if move.name == 'Scratch']) == 0
    assert len([move for move in results[1].moves if move.name == 'Tackle']) == 1


def load_game():
    # TODO: Get game data when new game is made, then data when the game is loaded from db. They should match
    pass

def test_get_last_game():
    game1 = new_game({0:1,1:2})
    game2 = new_game({0:2,1:1})

    last_game = get_last_game()

    get_pokemon = lambda x: last_game.pokemon[x].pokemon.id

    assert last_game.id == game2.id
    assert get_pokemon(0) == 2
    assert get_pokemon(1) == 1

def test_get_current_stat(setup_combatants):
    pokemon_a, x = setup_combatants
    data = pokemon_a.stats[Stat.ATTACK]
    data.base_stat = 50
    data.stage = 3
    result = pokemon_a.get_current_stat(Stat.ATTACK)
    assert result == 125


def test_save_current_stat(setup_combatants):
    pokemon_a, x = setup_combatants

    # Stage non-zero; save
    pokemon_a.stats[Stat.ATTACK].stage = 3
    result = save_combatant_stats(pokemon_a.id, pokemon_a.stats)
    assert len(result) == 1
    db_stats = get_combatant_stats(pokemon_a.id)
    assert len(db_stats) == 1
    assert Stat.ATTACK in db_stats[pokemon_a.id].keys()
    assert db_stats[pokemon_a.id][Stat.ATTACK].stage == 3

    # attack stat removed; defense is saved
    pokemon_a.stats[Stat.ATTACK].stage = 0
    pokemon_a.stats[Stat.DEFENSE].stage = -1
    result = save_combatant_stats(pokemon_a.id, pokemon_a.stats)
    assert len(result) == 1
    db_stats = get_combatant_stats(pokemon_a.id)
    assert len(db_stats) == 1
    assert Stat.ATTACK not in db_stats[pokemon_a.id].keys()
    assert Stat.DEFENSE in db_stats[pokemon_a.id].keys()
    assert db_stats[pokemon_a.id][Stat.DEFENSE].stage == -1


def test_use_move_on_pokemon_status(setup_combatants):
    pokemon_combatant, x = setup_combatants
    move = Move(**{
        "id":0,
        "name":'Status Move',
        "move_type":Type.NORMAL,
        "category":Category.STATUS,
        "move_power":None,
        "accuracy":100,
        "base_pp":5,
        "stat":Stat.ATTACK,
        "target_self":True,
        "stage_effect":2,
        "can_crit":False
    })

    result = use_move_on_pokemon(move, pokemon_combatant, pokemon_combatant)

    assert result != pokemon_combatant, "Original pokemon modified"
    assert result.id == pokemon_combatant.id

    assert pokemon_combatant.stats[Stat.ATTACK].stage == 0
    assert result.stats[Stat.ATTACK].stage == 2

    assert pokemon_combatant.get_current_stat(Stat.ATTACK) == 50
    assert result.get_current_stat(Stat.ATTACK) == 100

    result = use_move_on_pokemon(move, result, result) # stage is 4
    result = use_move_on_pokemon(move, result, result) # stage is 6
    result = use_move_on_pokemon(move, result, result) # stage (would be) 8

    # Stage cannot go above 6
    assert result.stats[Stat.ATTACK].stage == 6, "Stage should not got above magnitude of 6"

def test_use_move_on_pokemon_not_status(setup_combatants):
    attacker, defender = setup_combatants
    move = Move(**{
        "id":0,
        "name":'Physical Move',
        "move_type":Type.FIRE,
        "category":Category.PHYSICAL,
        "move_power":100,
        "accuracy":100,
        "base_pp":5,
        "stat":None,
        "target_self":None,
        "stage_effect":None,
        "can_crit":False
    })

    # Crit = 1, Power = 100, Attack = 50, Defense = 25, no STAB, no Type effect.
    # ((( ((2*Crit)/5 + 2) * Power * (Attack/Defense))/50 ) + 2) * STAB * Type * rand
    # ((( ((2*1)/5 + 2) * 100 * (50/25))/50 ) + 2) * 1 * 1 * rand
    # ((( (12/5) * 100 * 2)/50 ) + 2) * rand
    # 11.6 * rand
    result = use_move_on_pokemon(move, defender, attacker)

    # HP: 50 - 11.6 * rand; rand = 0.85 -> 1
    assert 41 >= result.hp_current >= 39

def test_things(setup_combatants):
    pass
