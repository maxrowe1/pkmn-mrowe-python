from flask import Flask
from flask_cors import CORS

from db_connect import get_all_pokemon, Pokemon
from pk_service import generate_combatant, get_game, new_game
from classes.Enums import Type

app = Flask(__name__)
CORS(app)

player = Pokemon({ "id": 0, "name":'', "type1":Type.NORMAL, "type2":None})

@app.route('/books/<player_id>', methods=['GET'])
def get_books(player_id):
    players = get_all_pokemon()
    global player
    print(f"Replace {player.id} with {player_id}")
    player = players[int(player_id)]
    return player

@app.route('/pokemon', methods=['GET'])
def get_all_pokemon():
    pokemon = get_all_pokemon()
    return [x.__dict__ for x in pokemon]

@app.route('/pokemon/<pokemon_id>/generate', methods=['GET'])
def generate_pokemon(pokemon_id):
    return generate_combatant(0, pokemon_id).__dict__

@app.route('/game', methods=['GET'])
def generate_new_game():
    return new_game({0: 1, 1: 2}).to_json()

@app.route('/game/<game_id>', methods=["GET"])
def get_game_by_id(game_id):
    return get_game(game_id).to_json()

if __name__ == '__main__':
    app.run(debug=False)
