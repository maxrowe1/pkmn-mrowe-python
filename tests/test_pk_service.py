from db_connect import Pokemon, Type, Move, Category, BaseStats
from pk_service import generate_combatant, generate_combatants, get_current_stat, StatData, PokemonData, \
    use_move_on_pokemon, Stat, PokemonCombatant


def test_generate_combatant():
    result1 = generate_combatant(1)
    assert result1.id == 1
    assert result1.name == 'Charmander'
    assert 98 <= result1.stats[Stat.ATTACK] <= 223
    assert result1.hp_max == result1.hp_max
    assert len(result1.moves) == 2

    # No two generations are the same (possible but unlikely)
    result2 = generate_combatant(2)
    assert result1 != result2
    assert (result1.stats[Stat.ATTACK] != result2.stats[Stat.ATTACK] or
            result1.stats[Stat.DEFENSE] != result2.stats[Stat.DEFENSE])


def test_generate_combatants():
    results = generate_combatants({0: 1, 1: 2})
    assert results[0].name == 'Charmander'
    assert results[1].name == 'Squirtle'
    assert len([move for move in results[0].moves if move.name == 'Scratch']) == 1
    assert len([move for move in results[0].moves if move.name == 'Tackle']) == 0
    assert len([move for move in results[1].moves if move.name == 'Scratch']) == 0
    assert len([move for move in results[1].moves if move.name == 'Tackle']) == 1


def test_get_current_stat():
    data = StatData(50, 3)
    result = get_current_stat(data)
    assert result == 125


def test_use_move_on_pokemon_status():
    pokemon = Pokemon(0, 'BeepBop', Type.NORMAL, None)
    move = Move(
        0,
        'Status Move',
        Type.NORMAL,
        Category.STATUS,
        None,
        100,
        5,
        Stat.ATTACK,
        True,
        2
    )
    stats = BaseStats(
        10,
        10,
        50,
        50,
        40,
        40,
        30,
        30,
        60,
        60,
        20,
        20
    )
    pokemon_data = PokemonData(pokemon, stats, [move])
    pokemon_combatant = PokemonCombatant(pokemon_data)
    result = use_move_on_pokemon(move, pokemon_combatant, pokemon_combatant)

    assert result != pokemon_combatant, "Original pokemon modified"

    assert pokemon_combatant.stats[Stat.ATTACK].stage == 0
    assert result.stats[Stat.ATTACK].stage == 2

    assert get_current_stat(pokemon_combatant.stats[Stat.ATTACK]) == 50
    assert get_current_stat(result.stats[Stat.ATTACK]) == 100

    result = use_move_on_pokemon(move, result, result) # stage is 4
    result = use_move_on_pokemon(move, result, result) # stage is 6
    result = use_move_on_pokemon(move, result, result) # stage (would be) 8

    # Stage cannot go above 6
    assert result.stats[Stat.ATTACK].stage == 6, "Stage should not got above magnitude of 6"

def test_use_move_on_pokemon_not_status():
    pokemon1 = Pokemon(0, 'BeepBop', Type.NORMAL, None)
    pokemon2 = Pokemon(0, 'Zorp', Type.NORMAL, None)
    move = Move(
        0,
        'Physical Move',
        Type.FIRE,
        Category.PHYSICAL,
        100,
        100,
        5,
        None,
        None,
        None,
        False
    )
    stats1 = BaseStats(
        200,
        200,
        50,
        50,
        60,
        60,
        30,
        30,
        100,
        100,
        20,
        20
    )
    stats2 = BaseStats(
        50,
        50,
        20,
        20,
        25,
        25,
        5,
        5,
        60,
        60,
        20,
        20
    )
    pokemon_data1 = PokemonData(pokemon1, stats1, [move])
    pokemon_data2 = PokemonData(pokemon2, stats2, [move])
    attacker = PokemonCombatant(pokemon_data1)
    defender = PokemonCombatant(pokemon_data2)

    # Crit = 1, Power = 100, Attack = 50, Defense = 25, no STAB, no Type effect.
    # ((( ((2*Crit)/5 + 2) * Power * (Attack/Defense))/50 ) + 2) * STAB * Type * rand
    # ((( ((2*1)/5 + 2) * 100 * (50/25))/50 ) + 2) * 1 * 1 * rand
    # ((( (12/5) * 100 * 2)/50 ) + 2) * rand
    # 11.6 * rand
    result = use_move_on_pokemon(move, defender, attacker)

    # HP: 50 - 11.6 * rand; rand = 0.85 -> 1
    assert 41 >= result.hp_current >= 39
