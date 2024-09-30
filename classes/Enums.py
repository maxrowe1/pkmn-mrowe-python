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

class Stat(Enum):
    ATTACK = "ATTACK"
    DEFENSE = "DEFENSE"
    SP_ATTACK = "SP_ATTACK"
    SP_DEFENSE = "SP_DEFENSE"
    SPEED = "SPEED"