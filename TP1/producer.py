import pika, uuid, json, random, time
from datetime import datetime, timezone

connection = pika.BlockingConnection(
    pika.ConnectionParameters('localhost')
)

channel = connection.channel()

channel.queue_declare(
    queue='hello',
    durable=True,
    arguments={'x-queue-type': 'quorum'}
)

tasks = ["payment", "email", "report", "update"]

start = time.time()

TOTAL = 5000

for i in range(TOTAL):
    message = {
        "event_id": str(uuid.uuid4()),
        "task": random.choice(tasks),
        "priority": random.randint(1, 10),
        "timestamp": datetime.now(timezone.utc).isoformat()
    }

    channel.basic_publish(
        exchange='',
        routing_key='hello',
        body=json.dumps(message).encode("utf-8")
    )

    if i % 500 == 0:
        print(f"Sent {i}")

end = time.time()

print(f"Done: {TOTAL} messages in {end - start:.2f}s")

connection.close()