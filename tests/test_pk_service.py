from pk_service import generate_combatant, generate_combatants


def test_generate_combatant():
    result1 = generate_combatant(1)
    assert result1.id == 1
    assert result1.name == 'Charmander'
    assert 98 <= result1.attack <= 223
    assert result1.hp == result1.hp
    assert len(result1.moves) == 2

    # No two generations are the same (possible but unlikely)
    result2 = generate_combatant(2)
    assert result1 != result2
    assert result1.attack != result2 or result1.defense != result2.defense


def test_generate_combatants():
    results = generate_combatants({0:1,1:2})
    assert results[0].name == 'Charmander'
    assert results[1].name == 'Squirtle'
    assert len([move for move in results[0].moves if move.name == 'Scratch']) == 1
    assert len([move for move in results[0].moves if move.name == 'Tackle']) == 0
    assert len([move for move in results[1].moves if move.name == 'Scratch']) == 0
    assert len([move for move in results[1].moves if move.name == 'Tackle']) == 1
