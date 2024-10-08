import logging
import os

import redis
import json

from flask.cli import load_dotenv

from src.utils.utils import is_local_testing

load_dotenv() # load environment variables

# Redis connection parameters
redis_config = {
    'host': os.getenv('REDIS_HOST'),
    'port': 6379,
    'db': 0
}

redis_running = False

logging.basicConfig(level=logging.INFO)

def is_redis_running():
    return redis_running

def manage_data_in_redis(redis_func):
    """
    :param redis_func:
    :return:
    """
    try:
        if not is_local_testing:
            # TODO: Redis on GitHub
            return

        # Connect to Redis
        r = redis.Redis(**redis_config)
        r.ping()

        global redis_running
        redis_running = True
        logging.info("Redis is running; will run redis command.")

        # Redis data management function
        return redis_func(r)
    except redis.ConnectionError:
        logging.error("REDIS IS NOT RUNNING. Direct calls to DB will be used.")


def store_data_in_redis(data):
    # store in redis
    manage_data_in_redis(lambda r: r.set(f"game_data{data.id}", json.dumps(data.to_json())))

def get_data_in_redis(game_id):
    data = manage_data_in_redis(lambda r: r.get(f"game_data{game_id}"))
    return json.loads(data) if data is not None else None