from collections import defaultdict

from psycopg2 import ProgrammingError
from psycopg2.extras import RealDictCursor

import settings
from classes.Enums import Stat
from enum import Enum

import psycopg2

from classes.BaseStats import BaseStats
from classes.Move import Move
from classes.Pokemon import Pokemon
from classes.PokemonCombatant import PokemonCombatant


def connect_to_database():
    conn = psycopg2.connect(database="postgres",
                            user="postgres",
                            host='localhost',
                            password="admin",
                            port=5432)
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    return conn, cursor

def execute_select_query(query):
    conn, cursor = connect_to_database()
    cursor.execute(query)
    results = cursor.fetchall()
    conn.close()
    return results

def execute_commit_query(query, values):
    new_rows = []
    conn, cursor = connect_to_database()

    for value in values:
        cursor.execute(query, value)
        try:
            new_rows.append(cursor.fetchone())
        except ProgrammingError as e:
            if "no results to fetch" not in repr(e):
                raise e

    if not settings.is_test():
        conn.commit()

    cursor.close()
    conn.close()
    return new_rows

def get_pokemon():
    results = execute_select_query('SELECT * FROM POKEMON')
    return [Pokemon(dict(x)) for x in results]

def get_pokemon_moves(*ids):
    results = execute_select_query(
        '''SELECT
            mv.pokemon_id,
            m.*
            FROM MOVES m LEFT JOIN POKEMON_MOVES mv ON m.ID = mv.MOVE_ID
            WHERE mv.POKEMON_ID IN ({0});'''.format(convert_int_tuple(ids))
    )
    pokemon_moves = defaultdict(list)
    for result in results:
        current_list = pokemon_moves[result["pokemon_id"]]
        if len(current_list) < 4:
            current_list.append(Move(result))
    return pokemon_moves

def get_pokemon_stats(*ids):
    pokemon_stats_map = {}
    results = execute_select_query(
        '''SELECT p.*, s.*
                FROM POKEMON p LEFT JOIN BASE_STATS s ON p.ID = s.POKEMON_ID 
                WHERE p.ID in ({0});'''.format(convert_int_tuple(ids))
        )
    for result in results:
        pokemon = Pokemon(result)
        pokemon_stats_map[pokemon.id] = {
            "pokemon": pokemon,
            "stats": BaseStats(result)
        }
    return pokemon_stats_map

def create_combatants(*combatants: PokemonCombatant):
    values_list = []
    columns = list(vars(combatants[0]))
    columns.remove("id")
    columns.remove("name")
    columns.remove("type1")
    columns.remove("type2")
    columns.remove("moves")
    columns.remove("types")
    columns.remove("stats")

    for stat in combatants[0].stats:
        columns.append(stat.value)

    columns = tuple(columns)

    for combatant in combatants:
        values = []
        combatant_dict = combatant.__dict__
        for column in columns:
            if column in combatant_dict.keys():
                value = combatant_dict[column]
                values.append((value if not isinstance(value, Enum) else value.value) if value is not None else None)
            else:
                values.append(combatant.stats[Stat[column]].base_stat)
        values_list.append(tuple(values))

    format_query_string = lambda x: str(x).replace("'","")

    new_combatants = execute_commit_query(
        """INSERT INTO combatants""" +
        format_query_string(columns) +
        """ VALUES""" +
        format_query_string(tuple(["%s" for x in range(0, len(columns))])) +
        """ RETURNING *""",
        values_list
    )

    updated_combatants = []
    for combatant in combatants:
        combatant.id = next(x for x in new_combatants if x["is_player"] == combatant.is_player)["id"]
        updated_combatants.append(combatant)

    return updated_combatants

def save_game(p_combatant_id, e_combatant_id):
    if settings.is_test():
        return
    execute_commit_query(
        """INSERT INTO games(p_combatant_id, e_combatant_id)
         VALUES (%s,%s)""", [(p_combatant_id, e_combatant_id)])

def delete_combatants(*combatant_ids):
    results = execute_commit_query("""DELETE FROM combatants WHERE id = %s;""", [(x,) for x in combatant_ids])
    assert len(results) == 0

def convert_int_tuple(ids):
    return ','.join([str(x) for x in ids])
