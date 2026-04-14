import pika, sys, os, json, psycopg2

def main():
    connection = pika.BlockingConnection(
        pika.ConnectionParameters(host='localhost')
    )

    channel = connection.channel()

    channel.queue_declare(
        queue='hello',
        durable=True,
        arguments={'x-queue-type': 'quorum'}
    )

    def callback(ch, method, properties, body):
        payload = json.loads(body.decode())
        print(f"Received {payload}")

        try:
            conn = psycopg2.connect(
                host="localhost",
                database="sistemas_distribuidos_tp1_db",
                user="user",
                password="password"
            )

            cur = conn.cursor()

            cur.execute(
                "INSERT INTO tasks (event_id, payload) VALUES (%s, %s)",
                (payload["event_id"], json.dumps(payload))
            )

            conn.commit()
            cur.close()
            conn.close()

            ch.basic_ack(delivery_tag=method.delivery_tag)

        except Exception as e:
            print("Error:", e)

    channel.basic_consume(
        queue='hello',
        on_message_callback=callback,
        auto_ack=False
    )

    print('Waiting for messages. To exit press CTRL+C')
    channel.start_consuming()


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print('Interrupted')
        try:
            sys.exit(0)
        except SystemExit:
            os._exit(0)