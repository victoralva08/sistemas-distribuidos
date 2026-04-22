"""
consumer_stock.py
-----------------
CONSUMIDOR DE ESTOQUE

Este script fica "escutando" a fila orders.stock esperando pedidos chegarem.
Quando um pedido chega, ele simula a reserva do produto no estoque.

Como funciona:
  1. Conecta ao RabbitMQ
  2. Se registra na fila orders.stock
  3. Para cada pedido, verifica se há produto disponível
  4. Envia ACK (confirmação) se reservado, ou NACK se estoque esgotado
     → Mensagens rejeitadas vão para a Dead Letter Queue (DLQ)

Execute com:
  python consumer_stock.py
"""

import pika
import json
import time
import random

# ── Configurações ──────────────────────────────────────────────────
RABBITMQ_HOST = "localhost"
RABBITMQ_USER = "admin"
RABBITMQ_PASS = "admin123"
FILA = "orders.stock"


def conectar():
    """Abre e retorna uma conexão com o RabbitMQ."""
    credentials = pika.PlainCredentials(RABBITMQ_USER, RABBITMQ_PASS)
    params = pika.ConnectionParameters(
        host=RABBITMQ_HOST,
        credentials=credentials,
        heartbeat=600,
    )
    return pika.BlockingConnection(params)


def processar_estoque(ch, method, properties, body):
    """
    Função chamada automaticamente pelo RabbitMQ a cada mensagem recebida.
    Simula a consulta e reserva de estoque para o pedido.
    """
    pedido = json.loads(body.decode("utf-8"))

    order_id    = pedido.get("order_id", "?")
    customer_id = pedido.get("customer_id", "?")
    product_id  = pedido.get("product_id", "?")
    quantity    = pedido.get("quantity", 1)

    # Simula o tempo de consulta ao sistema de estoque (10–30ms)
    time.sleep(random.uniform(0.01, 0.03))

    print(f"  [ESTOQUE] ✅ Reservado | {order_id} | {quantity}x {product_id} | Cliente {customer_id}")
    ch.basic_ack(delivery_tag=method.delivery_tag)


def main():
    print(f"[ESTOQUE] Conectando ao RabbitMQ e ouvindo a fila '{FILA}'...")
    print(f"[ESTOQUE] Aguardando pedidos. Pressione Ctrl+C para sair.\n")

    connection = conectar()
    channel = connection.channel()

    # prefetch_count=10 → controla quantas mensagens processa por vez (fair dispatch)
    channel.basic_qos(prefetch_count=10)

    channel.basic_consume(
        queue=FILA,
        on_message_callback=processar_estoque,
        auto_ack=False,
    )

    try:
        channel.start_consuming()
    except KeyboardInterrupt:
        print("\n[ESTOQUE] Encerrando...")
        channel.stop_consuming()

    connection.close()


if __name__ == "__main__":
    main()
