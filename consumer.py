import pika, sys, os
import psycopg2

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
        message = body.decode()
        print(f"Received {message}")

        try:
            conn = psycopg2.connect(
                host="localhost",
                database="tasks_db",
                user="user",
                password="password"
            )

            cur = conn.cursor()

            cur.execute(
                "INSERT INTO tasks (message) VALUES (%s)",
                (message,)
            )

            conn.commit()
            cur.close()
            conn.close()

            # ACK só depois de salvar
            ch.basic_ack(delivery_tag=method.delivery_tag)

        except Exception as e:
            print("Error:", e)
            # NÃO dá ack → mensagem volta pra fila

    channel.basic_consume(
        queue='hello',
        on_message_callback=callback,
        auto_ack=False  # ← MUITO IMPORTANTE
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