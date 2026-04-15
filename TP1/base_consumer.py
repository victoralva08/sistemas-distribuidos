"""
base_consumer.py – Classe base compartilhada por todos os consumers.
"""

import pika
import psycopg2
import json
import time

# ── Configurações ──────────────────────────────────────────────────
RABBITMQ_HOST = "localhost"
RABBITMQ_USER = "admin"
RABBITMQ_PASS = "admin123"

DB_CONFIG = {
    "host":     "localhost",
    "port":     5432,
    "dbname":   "ecommerce",
    "user":     "tp01",
    "password": "tp01pass",
}


def get_rabbit_connection():
    credentials = pika.PlainCredentials(RABBITMQ_USER, RABBITMQ_PASS)
    params = pika.ConnectionParameters(
        host=RABBITMQ_HOST,
        credentials=credentials,
        heartbeat=600,
        blocked_connection_timeout=300,
    )
    return pika.BlockingConnection(params)


def get_db_connection():
    return psycopg2.connect(**DB_CONFIG)


class BaseConsumer:
    """
    Consumer base com reconexão automática, ACK manual e métricas.
    Cada consumer especializado herda desta classe e implementa `process()`.
    """

    queue_name: str = ""
    consumer_tag: str = "consumer"
    prefetch_count: int = 10

    def __init__(self):
        self.processed = 0
        self.errors = 0
        self.start_time = time.time()
        self.db = get_db_connection()
        self.db.autocommit = False

    def process(self, payload: dict, ch, method) -> bool:
        """
        Implementar nos consumers filhos.
        Retornar True para ACK, False para NACK (vai para DLQ).
        """
        raise NotImplementedError

    def callback(self, ch, method, properties, body):
        try:
            payload = json.loads(body.decode("utf-8"))
            success = self.process(payload, ch, method)

            if success:
                ch.basic_ack(delivery_tag=method.delivery_tag)
                self.processed += 1
            else:
                # requeue=False → vai para a Dead Letter Queue
                ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)
                self.errors += 1

        except Exception as e:
            print(f"  [{self.consumer_tag}][ERRO] {e}")
            ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)
            self.errors += 1
            try:
                self.db.rollback()
            except Exception:
                pass

        # Log a cada 100 mensagens
        if (self.processed + self.errors) % 100 == 0:
            elapsed = time.time() - self.start_time
            rate = self.processed / elapsed if elapsed > 0 else 0
            print(
                f"  [{self.consumer_tag}] "
                f"Processadas: {self.processed} | "
                f"Erros: {self.errors} | "
                f"Taxa: {rate:.0f} msg/s"
            )

    def run(self):
        print(f"[{self.consumer_tag}] Conectando ao RabbitMQ...")
        connection = get_rabbit_connection()
        channel = connection.channel()

        # Limita mensagens não confirmadas por consumer (fair dispatch)
        channel.basic_qos(prefetch_count=self.prefetch_count)

        channel.basic_consume(
            queue=self.queue_name,
            on_message_callback=self.callback,
            auto_ack=False,
        )

        print(f"[{self.consumer_tag}] Ouvindo fila '{self.queue_name}'. Ctrl+C para sair.\n")
        try:
            channel.start_consuming()
        except KeyboardInterrupt:
            print(f"\n[{self.consumer_tag}] Encerrando...")
            channel.stop_consuming()

        connection.close()
        self.db.close()
        elapsed = time.time() - self.start_time
        print(f"[{self.consumer_tag}] Total: {self.processed} processadas | "
              f"{self.errors} erros | {elapsed:.1f}s")
