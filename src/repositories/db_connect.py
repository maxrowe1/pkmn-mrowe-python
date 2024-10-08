import os
from collections import defaultdict

from flask.cli import load_dotenv
from psycopg2 import ProgrammingError
from psycopg2.extras import RealDictCursor

from src.classes.Enums import Stat
from enum import Enum

import psycopg2

from src.classes.BaseStats import BaseStats
from src.classes.Move import Move
from src.classes.Pokemon import Pokemon
from src.classes.PokemonCombatant import PokemonCombatant, StatData
from src.classes.Game import Game

load_dotenv() # Load environment vars

def connect_to_database():
    conn = psycopg2.connect(database="postgres",
                            user="postgres",
                            host=os.getenv('DB_HOST'),
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
    return [Pokemon(**x) for x in results]

def get_pokemon(*pokemon_ids):
    results = execute_select_query(
        """
        SELECT *
        FROM POKEMON
        WHERE ID IN {0};
        """.format(convert_int_tuple(pokemon_ids))
    )
    return [Pokemon(**x) for x in results]

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
            current_list.append(Move(**result))
    return pokemon_moves

def get_pokemon_stats(*ids):
    pokemon_stats_map = {}
    results = execute_select_query(
        '''SELECT p.*, s.*
                FROM POKEMON p LEFT JOIN BASE_STATS s ON p.ID = s.POKEMON_ID 
                WHERE p.ID in ({0});'''.format(convert_int_tuple(ids))
        )
    for result in results:
        pokemon = Pokemon(**result)
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

    return Game(**results[0])

def get_last_game_saved():
    results = execute_select_query(
        """
        SELECT *
        FROM games
        ORDER BY modified_timestamp DESC
        LIMIT 1;
        """
    )

    if len(results) <= 0:
        raise Exception("No recent games found")

    return Game(**results[0])

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
    stat_changes_list = get_combatant_stats(*combatant_ids)

    def get_stat(stat: Stat):
        combatant_stats = stat_changes_list[combatant_id]
        return combatant_stats[stat] if stat in combatant_stats.keys() else StatData(combatant_result[stat.value.lower()])

    combatants = []
    for combatant_result in combatant_results:
        combatant_id = combatant_result["id"]
        pokemon = [x for x in pokemon_list if x.id == combatant_result["pokemon_id"]][0]
        moves = moves_list[combatant_id]
        stats = {
            Stat.ATTACK: get_stat(Stat.ATTACK),
            Stat.DEFENSE: get_stat(Stat.DEFENSE),
            Stat.SP_ATTACK: get_stat(Stat.SP_ATTACK),
            Stat.SP_DEFENSE: get_stat(Stat.SP_DEFENSE),
            Stat.SPEED: get_stat(Stat.SPEED)
        }
        combatant = PokemonCombatant(
            pokemon,
            stats,
            moves,
            id=combatant_id,
            hp_max=combatant_result["hp_max"],
            hp_current=combatant_result["hp_current"],
            is_player=combatant_result["is_player"]
        )
        combatants.append(combatant)
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
        combatant_moves_dict[combatant_id] = [Move(**x) for x in results if x["combatant_id"] == combatant_id]
    return combatant_moves_dict

def get_combatant_stats(*combatant_ids):
    results = execute_select_query(
        """
        SELECT s.*,
        CASE
            WHEN s.stat = 'ATTACK'::stats then c.attack
            WHEN s.stat = 'DEFENSE' then c.defense
            WHEN s.stat = 'SP_ATTACK' then c.sp_attack
            WHEN s.stat = 'SP_DEFENSE' then c.sp_defense
            WHEN s.stat = 'SPEED' then c.speed
            Else 0
        END as base_stat
        FROM combatant_stats s
        JOIN combatants c on c.id = s.combatant_id
        WHERE s.combatant_id IN ({0});
        """.format(convert_int_tuple(combatant_ids))
    )

    combatant_stats_dict = {}
    for combatant_id in combatant_ids:
        combatant_stats_dict[combatant_id] = {}
        for stat_data in [x for x in results if x["combatant_id"] == combatant_id]:
            combatant_stats_dict[combatant_id][Stat[stat_data["stat"]]] = (
                StatData(stat_data["base_stat"], stat_data["stage"]))
    return combatant_stats_dict

def create_combatants(*combatants: PokemonCombatant):
    remove_vars = ["id","pokemon","moves","types","stats"]
    add_vars = [x.value for x in combatants[0].stats]
    add_vars.append("pokemon_id")

    def append_stats(values, pc, column):
        values.append(pc.stats[Stat[column]].base_stat
                      if column in [x.value for x in Stat]
                      else pc.pokemon.id if column == "pokemon_id"
                      else pc.pokemon.__dict__[column]
                      )

    new_combatants = execute_insert_query("combatants", combatants, add_vars, remove_vars, append_stats)

    updated_combatants = []
    for combatant in combatants:
        combatant.id = next(x for x in new_combatants if x["is_player"] == combatant.is_player)["id"]
        combatant.moves = save_combatant_moves(combatant.id, combatant.moves)
        save_combatant_stats(combatant.id, combatant.stats)
        updated_combatants.append(combatant)

    return updated_combatants


def save_combatant_moves(combatant_id, moves):
    add_vars = ["combatant_id", "move_id", "move_number", "pp_current"]

    def append_data(values, cm, column):
        cm_object: Move = [x for x in moves if x.id == cm["move_id"]][0]
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
        "combatant_moves", [{"move_id":moves[x].id} for x in range(0, len(moves))], add_vars, [], append_data)

    updated_moves = []
    for move in moves:
        new_combatant_move = next(x for x in new_combatant_moves if x["move_id"] == move.id)
        move.set_combatant_data(**new_combatant_move)
        updated_moves.append(move)

    return updated_moves


def save_combatant_stats(combatant_id, stats):
    # Remove existing stats from DB
    execute_commit_query("""DELETE FROM combatant_stats WHERE combatant_id = %s;""", [(combatant_id,)])

    insert_list = [{"combatant_id":combatant_id, "stat":x, "stage":y.stage} for x,y in stats.items() if y.stage != 0]
    new_combatant_stats = execute_insert_query(
        "combatant_stats", insert_list, [], []
    )

    saved_stats = {}
    for stat_data in new_combatant_stats:
        stat = Stat[stat_data["stat"]]
        saved_stats[stat] = StatData(stats[stat].base_stat, stat_data["stage"])
    return saved_stats


def execute_insert_query(table_name, insert_list, add_vars, remove_vars, append_extra = None):

    columns = [] if len(insert_list) <= 0 else list(insert_list[0].keys()) if isinstance(insert_list[0], dict) else list(vars(insert_list[0])) if '__dict__' in dir(insert_list[0]) else []

    def adjust(var_list, func):
        for var in var_list:
            func(var)
    adjust(remove_vars, columns.remove)
    adjust(add_vars, columns.append)

    columns = tuple(set(columns))

    values_list = []
    for insert_object in insert_list:
        values = []
        value_dict = insert_object if isinstance(insert_object, dict) else insert_object.__dict__ if '__dict__' in dir(insert_object) else {}
        for column in columns:
            if column in value_dict.keys():
                # values from surface-level attributes
                value = value_dict[column]
                values.append((value if not isinstance(value, Enum) else value.value) if value is not None else None)
            else:
                # special logic for nested data
                if append_extra is not None:
                    append_extra(values, insert_object, column)

        assert len(columns) == len(values), f"Columns({len(columns)} != Values({len(values)})"
        values_list.append(tuple(values))


    format_query_string = lambda x: str(x).replace("'", "")

    new_combatants = execute_commit_query(
        f"""INSERT INTO {table_name} """ +
        format_query_string(columns) +
        """ VALUES""" +
        format_query_string(tuple(["%s"] * len(columns))) +
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
    return Game(**result)

def delete_combatants(*combatant_ids):
    results = execute_commit_query("""DELETE FROM combatants WHERE id = %s;""", [(x,) for x in combatant_ids])
    assert len(results) == 0

def convert_int_tuple(ids):
    return ','.join([str(x) for x in ids])
