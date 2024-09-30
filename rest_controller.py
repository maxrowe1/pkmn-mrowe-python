from flask import Flask
from flask_cors import CORS
from db_connect import get_pokemon, Pokemon, Type
from pk_service import generate_combatant, generate_combatants

app = Flask(__name__)
CORS(app)

player = Pokemon(0, '', Type.NORMAL, None)

@app.route('/books/<player_id>', methods=['GET'])
def get_books(player_id):
    players = get_pokemon()
    global player
    print(f"Replace {player.id} with {player_id}")
    player = players[int(player_id)]
    return player

@app.route('/pokemon', methods=['GET'])
def get_all_pokemon():
    pokemon = get_pokemon()
    return [x.__dict__ for x in pokemon]

@app.route('/pokemon/<pokemon_id>/generate', methods=['GET'])
def generate_pokemon(pokemon_id):
    return generate_combatant(pokemon_id).__dict__

@app.route('/game', methods=['GET'])
def generate_new_game():
    response = {}
    combatants_map = generate_combatants({0: 1, 1: 2})
    for player_id, combatant in combatants_map.items():
        response[player_id] = combatant.to_json()
    return response

if __name__ == '__main__':
    app.run(debug=False)
