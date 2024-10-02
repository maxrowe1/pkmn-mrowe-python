from redis_connect import store_data_in_redis
from utils import jsonify_dict


class GameComplete:
    def __init__(self, game_id, pokemon: dict):
        self.id = int(game_id)
        self.pokemon = pokemon
        store_data_in_redis(self)

    def to_json(self):
        self.pokemon = jsonify_dict(self.pokemon)
        return self.__dict__