from collections import defaultdict

from psycopg2 import ProgrammingError
from psycopg2.extras import RealDictCursor

from classes.Enums import Stat
from enum import Enum

import psycopg2

from classes.BaseStats import BaseStats
from classes.Move import Move
from classes.Pokemon import Pokemon
from classes.PokemonCombatant import PokemonCombatant
from classes.Game import Game
from utils import get_player_or_enemy_id


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

    conn.commit()
    cursor.close()
    conn.close()
    return new_rows

def get_all_pokemon():
    results = execute_select_query('SELECT * FROM POKEMON')
    return [Pokemon(dict(x)) for x in results]

def get_pokemon(*pokemon_ids):
    results = execute_select_query(
        """
        SELECT *
        FROM POKEMON
        WHERE ID IN {0};
        """.format(convert_int_tuple(pokemon_ids))
    )
    return [Pokemon(x) for x in results]

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

def get_game_data(game_id):
    results = execute_select_query(
        """
        SELECT g.*
        FROM games g
        WHERE g.ID = {0};
        """.format(game_id)
    )

    if len(results) <= 0:
        raise Exception("Group ID was not found")

    return Game(results[0])

def get_combatant_data(*combatant_ids):
    combatant_results = execute_select_query(
        """
        SELECT *
        FROM combatants
        WHERE ID IN ({0});
        """.format(convert_int_tuple(combatant_ids))
    )

    pokemon_list = get_pokemon(tuple([x["pokemon_id"] for x in combatant_results]))
    moves_list = get_combatant_moves(*combatant_ids)

    combatants = {}
    for combatant_result in combatant_results:
        combatant_id = combatant_result["id"]
        pokemon = [x for x in pokemon_list if x.id == combatant_result["pokemon_id"]][0]
        moves = moves_list[combatant_id]
        stats = {
            "hp_current": combatant_result["hp_current"],
            "hp_max": combatant_result["hp_max"],
            "is_player": combatant_result["is_player"],
            "stat_list": {
                # TODO: BaseStat with stored stage value
                Stat.ATTACK: combatant_result["attack"],
                Stat.DEFENSE: combatant_result["defense"],
                Stat.SP_ATTACK: combatant_result["sp_attack"],
                Stat.SP_DEFENSE: combatant_result["sp_defense"],
                Stat.SPEED: combatant_result["speed"]
            }
        }
        combatant = PokemonCombatant(pokemon, stats, moves, combatant_id)
        combatants[get_player_or_enemy_id(combatant)] = combatant
    return combatants

def get_combatant_moves(*combatant_ids):
    results = execute_select_query(
        """
        SELECT 
            c.combatant_id,
            c.move_number,
            c.pp_current,
            m.*
        FROM combatant_moves c
        LEFT JOIN moves m ON m.id = c.move_id 
        WHERE c.combatant_id IN ({0});
        """.format(convert_int_tuple(combatant_ids))
    )
    combatant_moves_dict = {}
    for combatant_id in combatant_ids:
        combatant_moves_dict[combatant_id] = [Move(x) for x in results if x["combatant_id"] == combatant_id]
    return combatant_moves_dict

def create_combatants(*combatants: PokemonCombatant):
    remove_vars = ["id","name","type1","type2","moves","types","stats"]
    add_vars = [x.value for x in combatants[0].stats]

    append_stats = lambda values, pc, column: values.append(pc.stats[Stat[column]].base_stat)

    new_combatants = execute_insert_query("combatants", combatants, add_vars, remove_vars, append_stats)

    updated_combatants = []
    for combatant in combatants:
        combatant.id = next(x for x in new_combatants if x["is_player"] == combatant.is_player)["id"]
        updated_combatants.append(combatant)

    return updated_combatants


def save_combatant_moves(combatant_id, moves):
    add_vars = ["combatant_id", "move_id", "move_number", "pp_current"]

    def append_data(values, cm, column):
        cm_object: Move = [x for x in moves if x.id == cm["id"]][0]
        match column:
            case "combatant_id":
                values.append(combatant_id)
            case "move_id":
                values.append(cm["id"])
            case "move_number":
                values.append(moves.index(cm_object) + 1)
            case "pp_current":
                values.append(cm_object.base_pp)

    new_combatant_moves = execute_insert_query(
        "combatant_moves", [{"id":moves[x].id} for x in range(0, len(moves))], add_vars, [], append_data)

    updated_moves = []
    for move in moves:
        new_combatant_move = next(x for x in new_combatant_moves if x["move_id"] == move.id)
        move.set_combatant_data(new_combatant_move)
        updated_moves.append(move)

    return updated_moves


def execute_insert_query(table_name, insert_list, add_vars, remove_vars, append_extra = None):

    columns = list(vars(insert_list[0])) if len(insert_list) > 0 and '__dict__' in dir(insert_list[0]) else []

    def adjust(var_list, func):
        for var in var_list:
            func(var)
    adjust(remove_vars, columns.remove)
    adjust(add_vars, columns.append)

    columns = tuple(columns)

    values_list = []
    for insert_object in insert_list:
        values = []
        value_dict = insert_object.__dict__ if '__dict__' in dir(insert_object) else {}
        for column in columns:
            if column in value_dict.keys():
                # values from surface-level attributes
                value = value_dict[column]
                values.append((value if not isinstance(value, Enum) else value.value) if value is not None else None)
            else:
                # special logic for nested data
                if append_extra is not None:
                    append_extra(values, insert_object, column)

        assert len(columns) == len(values)
        values_list.append(tuple(values))


    format_query_string = lambda x: str(x).replace("'", "")

    new_combatants = execute_commit_query(
        """INSERT INTO """ + table_name + """ """ +
        format_query_string(columns) +
        """ VALUES""" +
        format_query_string(tuple(["%s" for x in range(0, len(columns))])) +
        """ RETURNING *""",
        values_list
    )
    return new_combatants

def save_game(p_combatant_id, e_combatant_id):
    result = execute_commit_query(
        """INSERT INTO 
        games(p_combatant_id, e_combatant_id)
        VALUES (%s,%s)
        RETURNING *""",
        [(p_combatant_id, e_combatant_id)])[0]
    return Game(result)

def delete_combatants(*combatant_ids):
    results = execute_commit_query("""DELETE FROM combatants WHERE id = %s;""", [(x,) for x in combatant_ids])
    assert len(results) == 0

def convert_int_tuple(ids):
    return ','.join([str(x) for x in ids])
