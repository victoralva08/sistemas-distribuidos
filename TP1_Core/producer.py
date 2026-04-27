"""
producer.py
-----------
Minimal producer: sends messages to RabbitMQ queue.
"""

import pika
import json
import uuid
import random
import sys

# RabbitMQ Configuration
HOST = "localhost"
USER = "admin"
PASS = "admin123"
EXCHANGE = "orders"
QUEUE_PAYMENT = "orders.payment"
QUEUE_STOCK = "orders.stock"
QUEUE_NOTIFICATION = "orders.notification"


def connect():
    """Connect to RabbitMQ."""
    credentials = pika.PlainCredentials(USER, PASS)
    params = pika.ConnectionParameters(host=HOST, credentials=credentials)
    return pika.BlockingConnection(params)


def setup(channel):
    """Declare exchange and queues."""
    # Exchange
    channel.exchange_declare(exchange=EXCHANGE, exchange_type='fanout', durable=True)
    
    # Queues
    channel.queue_declare(queue=QUEUE_PAYMENT, durable=True)
    channel.queue_declare(queue=QUEUE_STOCK, durable=True)
    channel.queue_declare(queue=QUEUE_NOTIFICATION, durable=True)
    
    # Bindings
    channel.queue_bind(exchange=EXCHANGE, queue=QUEUE_PAYMENT)
    channel.queue_bind(exchange=EXCHANGE, queue=QUEUE_STOCK)
    channel.queue_bind(exchange=EXCHANGE, queue=QUEUE_NOTIFICATION)


def produce(count=100):
    """Send N messages to RabbitMQ."""
    connection = connect()
    channel = connection.channel()
    setup(channel)
    
    print(f"[PRODUCER] Sending {count} messages...\n")
    
    for i in range(1, count + 1):
        message = {
            "id": str(uuid.uuid4()),
            "order_number": i,
            "customer": f"CUST-{random.randint(1000, 9999)}",
            "product": random.choice(["notebook", "phone", "tablet"]),
            "quantity": random.randint(1, 5),
            "price": round(random.uniform(100, 5000), 2)
        }
        
        body = json.dumps(message)
        channel.basic_publish(exchange=EXCHANGE, routing_key='', body=body)
        
        if i % 10 == 0 or i == count:
            print(f"  ✓ Sent {i}/{count} messages")
    
    print(f"\n[PRODUCER] Done! All {count} messages sent.\n")
    connection.close()


if __name__ == "__main__":
    count = int(sys.argv[1]) if len(sys.argv) > 1 else 100
    produce(count)
