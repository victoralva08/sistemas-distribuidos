"""
consumer_notification.py
------------------------
Minimal consumer: listens to notification queue and processes messages.
"""

import pika
import json

HOST = "localhost"
USER = "admin"
PASS = "admin123"
QUEUE = "orders.notification"


def connect():
    """Connect to RabbitMQ."""
    credentials = pika.PlainCredentials(USER, PASS)
    params = pika.ConnectionParameters(host=HOST, credentials=credentials)
    return pika.BlockingConnection(params)


def callback(ch, method, properties, body):
    """Process message."""
    message = json.loads(body)
    print(f"[NOTIFICATION] Sending confirmation for order #{message['order_number']} to {message['customer']}")
    ch.basic_ack(delivery_tag=method.delivery_tag)


def consume():
    """Listen to queue."""
    connection = connect()
    channel = connection.channel()
    channel.queue_declare(queue=QUEUE, durable=True)
    channel.basic_consume(queue=QUEUE, on_message_callback=callback)
    
    print(f"[NOTIFICATION] Listening to queue '{QUEUE}'... Press Ctrl+C to exit\n")
    channel.start_consuming()


if __name__ == "__main__":
    consume()
