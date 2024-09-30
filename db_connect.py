from collections import defaultdict

import psycopg2
from enum import Enum

class Type(Enum):
    NORMAL = 'NORMAL'
    FIRE = 'FIRE'
    WATER = 'WATER'
    ELECTRIC = 'ELECTRIC'
    GRASS = 'GRASS'
    ICE = 'ICE'
    FIGHTING = 'FIGHTING'
    POISON = 'POISON'
    GROUND = 'GROUND'
    FLYING = 'FLYING'
    PSYCHIC = 'PSYCHIC'
    BUG = 'BUG'
    ROCK = 'ROCK'
    GHOST = 'GHOST'
    DRAGON = 'DRAGON'
    DARK = 'DARK'
    STEEL = 'STEEL'
    FAIRY = 'FAIRY'

class Category(Enum):
    PHYSICAL = "PHYSICAL"
    SPECIAL = "SPECIAL"
    STATUS = "STATUS"

class Pokemon:
    def __init__(self, pokemon_id, name, type1, type2):
        self.id = pokemon_id
        self.name = name
        self.type1 = type1
        self.type2 = type2

class Move:
    def __init__(
            self,
            move_id,
            name,
            move_type,
            category,
            power,
            accuracy,
            base_pp,
            stat,
            target_self,
            stage_effect,
            can_crit = True
    ):
        self.id = move_id
        self.name = name
        self.type = move_type
        self.category = category
        self.power = power
        self.accuracy = accuracy
        self.base_pp = base_pp
        self.stat = stat
        self.target_self = target_self
        self.stage_effect = stage_effect
        self.can_crit = can_crit

class BaseStats:
    def __init__(
            self,
            hp_min,
            hp_max,
            attack_min,
            attack_max,
            defense_min,
            defense_max,
            sp_attack_min,
            sp_attack_max,
            sp_defense_min,
            sp_defense_max,
            speed_min,
            speed_max):
        self.hp_min = hp_min
        self.hp_max = hp_max
        self.attack_min = attack_min
        self.attack_max = attack_max
        self.defense_min = defense_min
        self.defense_max = defense_max
        self.sp_attack_min = sp_attack_min
        self.sp_attack_max = sp_attack_max
        self.sp_defense_min = sp_defense_min
        self.sp_defense_max = sp_defense_max
        self.speed_min = speed_min
        self.speed_max = speed_max

def connect_to_database():
    conn = psycopg2.connect(database="postgres",
                            user="postgres",
                            host='localhost',
                            password="admin",
                            port=5432)
    cursor = conn.cursor()
    return conn, cursor

def execute_select_query(query):
    conn, cursor = connect_to_database()
    cursor.execute(query)
    results = cursor.fetchall()
    conn.close()
    return results

def execute_commit_query(query, *ids):
    conn, cursor = connect_to_database()
    cursor.executemany(query, [(x,) for x in ids])
    conn.commit()
    cursor.close()
    conn.close()

def parse_pokemon(x):
    return Pokemon(x[0], x[1], x[2], x[3])

def get_pokemon():
    results = execute_select_query('SELECT * FROM POKEMON')
    return [parse_pokemon(x) for x in results]

def get_pokemon_moves(*ids):
    results = execute_select_query(
        '''SELECT
            mv.pokemon_id,
            m.id,
            m.name,
            m.move_type,
            m.category,
            m.move_power,
            m.accuracy,
            m.base_pp,
            m.stat,
            m.target_self,
            m.stage_effect 
            FROM MOVES m LEFT JOIN POKEMON_MOVES mv ON m.ID = mv.MOVE_ID
            WHERE mv.POKEMON_ID IN ({});'''.format(convert_int_tuple(ids))
    )
    pokemon_moves = defaultdict(list)
    for result in results:
        current_list = pokemon_moves[result[0]]
        if len(current_list) < 4:
            current_list.append(
                Move(result[1], result[2], result[3], result[4], result[5], result[6], result[7], result[8], result[9], result[10]))
    return pokemon_moves

def get_pokemon_stats(*ids):
    pokemon_stats_map = {}
    results = execute_select_query(
        '''SELECT p.id, p.name, p.type1, p.type2, 
                s.HP_MIN,
                s.HP_MAX,
                s.ATTACK_MIN ,
                s.ATTACK_MAX ,
                s.DEFENSE_MIN ,
                s.DEFENSE_MAX ,
                s.SP_ATTACK_MIN,
                s.SP_ATTACK_MAX,
                s.SP_DEFENSE_MIN,
                s.SP_DEFENSE_MAX,
                s.SPEED_MIN,
                s.SPEED_MAX
                FROM POKEMON p LEFT JOIN BASE_STATS s ON p.ID = s.POKEMON_ID 
                WHERE p.ID in ({0});'''.format(convert_int_tuple(ids))
        )
    for result in results:
        pokemon = parse_pokemon(result)
        pokemon_stats_map[pokemon.id] = {
            "pokemon": pokemon,
            "stats": BaseStats(
                result[4], result[5],
                result[6], result[7],
                result[8], result[9],
                result[10], result[11],
                result[12], result[13],
                result[14], result[15],
            )
        }
    return pokemon_stats_map

def delete_combatants(*combatant_ids):
    execute_commit_query("""DELETE FROM combatants WHERE id = %s;""", *combatant_ids)

def convert_int_tuple(ids):
    return ','.join([str(x) for x in ids])
