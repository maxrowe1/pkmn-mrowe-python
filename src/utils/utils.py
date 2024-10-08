from enum import Enum


def jsonify_dict(dict_: dict):
    return {k: v for d in
            [{x.value if isinstance(x, Enum) else x:y.to_json() if 'to_json' in dir(y) else y.__dict__ if '__dict__' in dir(y) else y} for x,y in dict_.items()]
            for k, v in d.items()}

get_player_or_enemy_id = lambda combatant: 0 if combatant.is_player else 1