import pika

connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
channel = connection.channel()

message = 'Hello, World!'

channel.queue_declare(queue='hello', durable=True, arguments={'x-queue-type': 'quorum'})
channel.basic_publish(exchange='',
                      routing_key='hello',
                      body=message)
print(f"Sent {message}")

connection.close()