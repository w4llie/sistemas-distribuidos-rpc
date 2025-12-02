# common/rpc_utils.py
import pika
import os

RABBIT_HOST = os.environ.get("RABBIT_HOST", "localhost")

def get_connection():
    params = pika.ConnectionParameters(host=RABBIT_HOST)
    return pika.BlockingConnection(params)
