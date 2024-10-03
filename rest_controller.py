import json
import threading
from types import SimpleNamespace

from confluent_kafka import Consumer, KafkaError
from flask import Flask
from flask_cors import CORS

from classes.GameComplete import GameComplete
from db_connect import get_all_pokemon
from pk_service import generate_combatant, get_game, new_game, get_last_game

app = Flask(__name__)
CORS(app)

# Kafka consumer configuration
conf = {
    'bootstrap.servers': 'localhost:9092',  # Kafka broker address
    'group.id': 'my-group',                   # Consumer group ID
    'auto.offset.reset': 'earliest'           # Start reading from the earliest message
}

# Create a Kafka consumer instance
consumer = Consumer(conf)

# Global variable to store consumed messages
messages = []

# Function to consume messages from Kafka
def consume_messages():
    consumer.subscribe(['pokemon_moves'])  # Replace 'test' with your topic name
    while True:
        msg = consumer.poll(1.0)  # Timeout of 1 second
        if msg is None:
            continue
        if msg.error():
            if msg.error().code() == KafkaError._PARTITION_EOF:
                continue
            else:
                print(f'Error while consuming message: {msg.error()}')
                continue

        # Store the message
        json_message = json.loads(msg.value().decode('utf-8'))
        data = GameComplete(**json_message)
        print(data)

# Start the Kafka consumer in a separate thread
threading.Thread(target=consume_messages, daemon=True).start()

@app.route('/pokemon', methods=['GET'])
def get_all_pokemon():
    pokemon = get_all_pokemon()
    return [x.__dict__ for x in pokemon]

@app.route('/pokemon/<pokemon_id>/generate', methods=['POST'])
def generate_pokemon(pokemon_id):
    return generate_combatant(0, pokemon_id).__dict__

@app.route('/game/new', methods=['POST'])
def generate_new_game():
    return new_game({0: 1, 1: 2}).to_json()

@app.route('/game/<game_id>', methods=["GET"])
def get_game_by_id(game_id):
    return get_game(game_id).to_json()

@app.route('/game/last', methods=["GET"])
def get_last_game_played():
    return get_last_game().to_json()

if __name__ == '__main__':
    app.run(debug=False)
