import pika
import uuid
import json
import random
import time
import argparse
from datetime import datetime, timezone

# ── Configurações ──────────────────────────────────────────────────
RABBITMQ_HOST = "localhost"
RABBITMQ_USER = "admin"
RABBITMQ_PASS = "admin123"
EXCHANGE_NAME  = "orders.exchange"

ROUTING_KEYS = [
    "order.payment.new",
    "order.stock.reserve",
    "order.notify.confirm",
    "order.audit.log",
]

PRODUCTS = ["notebook", "smartphone", "tablet", "monitor", "headset", "keyboard", "mouse"]


def get_connection():
    credentials = pika.PlainCredentials(RABBITMQ_USER, RABBITMQ_PASS)
    params = pika.ConnectionParameters(
        host=RABBITMQ_HOST,
        credentials=credentials,
        heartbeat=600,
        blocked_connection_timeout=300,
    )
    return pika.BlockingConnection(params)


def setup_infrastructure(channel):
    """Declara o exchange, filas e bindings."""

    # Topic Exchange principal
    channel.exchange_declare(
        exchange=EXCHANGE_NAME,
        exchange_type="topic",
        durable=True,
    )

    # Dead Letter Exchange
    channel.exchange_declare(
        exchange="orders.dlx",
        exchange_type="fanout",
        durable=True,
    )

    # Dead Letter Queue
    channel.queue_declare(
        queue="orders.dlq",
        durable=True,
    )
    channel.queue_bind(exchange="orders.dlx", queue="orders.dlq")

    queue_args = {
        "x-queue-type":           "quorum",
        "x-dead-letter-exchange": "orders.dlx",
        "x-message-ttl":          60000,   # 60s de TTL
    }

    filas = [
        ("orders.payment",      "order.payment.*"),
        ("orders.stock",        "order.stock.*"),
        ("orders.notification", "order.notify.*"),
        ("orders.audit",        "order.#"),      # captura TUDO
    ]

    for fila, routing_pattern in filas:
        channel.queue_declare(queue=fila, durable=True, arguments=queue_args)
        channel.queue_bind(
            exchange=EXCHANGE_NAME,
            queue=fila,
            routing_key=routing_pattern,
        )

    print("[SETUP] Exchange, filas e bindings configurados.")


def build_message(order_id: int) -> dict:
    return {
        "event_id":   str(uuid.uuid4()),
        "order_id":   f"ORD-{order_id:06d}",
        "customer_id": f"CUST-{random.randint(1, 500):04d}",
        "product_id": random.choice(PRODUCTS),
        "quantity":   random.randint(1, 5),
        "amount":     round(random.uniform(19.99, 4999.99), 2),
        "timestamp":  datetime.now(timezone.utc).isoformat(),
    }


def run(total: int, batch_report: int = 1000):
    print(f"[PRODUCER] Conectando ao RabbitMQ em {RABBITMQ_HOST}...")
    connection = get_connection()
    channel = connection.channel()

    # Confirmação de entrega (publisher confirms)
    channel.confirm_delivery()

    setup_infrastructure(channel)

    print(f"[PRODUCER] Enviando {total:,} mensagens...\n")

    start = time.time()
    errors = 0

    for i in range(1, total + 1):
        routing_key = random.choice(ROUTING_KEYS)
        message = build_message(i)
        body = json.dumps(message).encode("utf-8")

        try:
            channel.basic_publish(
                exchange=EXCHANGE_NAME,
                routing_key=routing_key,
                body=body,
                properties=pika.BasicProperties(
                    delivery_mode=2,          # persistente
                    content_type="application/json",
                    message_id=message["event_id"],
                ),
                mandatory=True,
            )
        except Exception as e:
            errors += 1
            print(f"  [ERRO] Mensagem {i}: {e}")
            continue

        if i % batch_report == 0:
            elapsed = time.time() - start
            rate = i / elapsed
            print(f"  Enviadas: {i:>7,} | Tempo: {elapsed:>6.1f}s | Taxa: {rate:>8.0f} msg/s")

    elapsed = time.time() - start
    rate = total / elapsed

    print(f"\n{'='*55}")
    print(f"  TOTAL ENVIADO : {total:,} mensagens")
    print(f"  ERROS         : {errors}")
    print(f"  TEMPO TOTAL   : {elapsed:.2f}s")
    print(f"  TAXA MEDIA    : {rate:.0f} msg/s")
    print(f"{'='*55}")

    connection.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="RabbitMQ Producer – TP01")
    parser.add_argument("--total", type=int, default=10000,
                        help="Total de mensagens a enviar (default: 10000)")
    parser.add_argument("--report", type=int, default=1000,
                        help="Intervalo de relatório (default: 1000)")
    args = parser.parse_args()

    run(total=args.total, batch_report=args.report)