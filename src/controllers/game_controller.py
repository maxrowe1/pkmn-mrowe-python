import atexit
import logging
import os
import threading
import traceback
from json import JSONDecodeError

from confluent_kafka import Consumer, KafkaError
from flask import Flask
from flask.cli import load_dotenv
from flask_cors import CORS

from src.repositories.db_connect import get_all_pokemon
from src.services.pk_service import generate_combatant, get_game, new_game, get_last_game, get_game_from_json
from src.utils.constants import kafka_topic

app = Flask(__name__)
CORS(app)

load_dotenv() # load environment variables

# Kafka consumer configuration
conf = {
    'bootstrap.servers': os.getenv('KAFKA_HOST'),  # Kafka broker address
    'group.id': 'my-group',                   # Consumer group ID
    'auto.offset.reset': 'earliest'           # Start reading from the earliest message
}

# Create a Kafka consumer instance
consumer = Consumer(conf)
consumer.subscribe([kafka_topic])

def cleanup():
    print("Closing the stream")
    consumer.close()
atexit.register(cleanup)

# Function to consume messages from Kafka
def consume_messages():
    msg = None
    while True:
        try:
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
            message = msg.value().decode('utf-8')
            print(get_game_from_json(message).to_json())
        except (JSONDecodeError, TypeError, ValueError) as e:
            logging.error(f"Failed to read kafka message:\n{msg}\n{str(e)}\n{traceback.format_exc()}")

# Start the Kafka consumer in a separate thread
threading.Thread(target=consume_messages, daemon=True).start()

@app.route('/pokemon', methods=['GET'])
def get_all_pokemon_():
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
