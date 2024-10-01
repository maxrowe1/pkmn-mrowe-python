from utils import jsonify_dict


class GameComplete:
    def __init__(self, game_id, pokemon: dict):
        self.id = int(game_id)
        self.pokemon = pokemon

    def to_json(self):
        self.pokemon = jsonify_dict(self.pokemon)
        return self.__dict__