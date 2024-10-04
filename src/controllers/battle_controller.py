import logging

from confluent_kafka import Producer
from flask import Flask, jsonify, request
from flask_cors import CORS
import json

from src.utils.constants import kafka_topic

app = Flask(__name__)
CORS(app)

# Configure the Kafka producer
conf = {
    'bootstrap.servers': 'localhost:9092',  # Adjust based on your Kafka setup
}
producer = Producer(**conf)

@app.route('/battle/update', methods=['PUT', 'OPTIONS'])
def update_game():
    if request.method == 'OPTIONS':
        # CORS preflight response
        return '', 200

    try:
        # TODO: Get game object after attack
        data = request.get_json()

        # Produce the message to Kafka
        producer.produce(kafka_topic, json.dumps(data))
        producer.flush()  # Wait for any outstanding messages to be delivered

        return jsonify({"status": "Message sent successfully"}), 200
    except Exception as e:
        logging.error(f"Issue with kafka message:\n{str(e)}")
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5050)  # Run on port 5000