"""
consumer_notification.py
------------------------
CONSUMIDOR DE NOTIFICAÇÕES

Este script fica "escutando" a fila orders.notification esperando pedidos.
Quando um pedido chega, ele simula o envio de uma notificação ao cliente
(pode ser e-mail, SMS ou push notification).

Como funciona:
  1. Conecta ao RabbitMQ
  2. Se registra na fila orders.notification
  3. Para cada pedido, escolhe um canal de contato e "envia" a notificação
  4. Envia ACK (confirmação) se entregue, ou NACK se falhou

Execute com:
  python consumer_notification.py
"""

import pika
import json
import time
import random

# ── Configurações ──────────────────────────────────────────────────
RABBITMQ_HOST = "localhost"
RABBITMQ_USER = "admin"
RABBITMQ_PASS = "admin123"
FILA = "orders.notification"

# Canais de comunicação disponíveis para notificar o cliente
CANAIS = ["email", "sms", "push"]


def conectar():
    """Abre e retorna uma conexão com o RabbitMQ."""
    credentials = pika.PlainCredentials(RABBITMQ_USER, RABBITMQ_PASS)
    params = pika.ConnectionParameters(
        host=RABBITMQ_HOST,
        credentials=credentials,
        heartbeat=600,
    )
    return pika.BlockingConnection(params)


def processar_notificacao(ch, method, properties, body):
    """
    Função chamada automaticamente pelo RabbitMQ a cada mensagem recebida.
    Simula o envio de notificação por e-mail, SMS ou push.
    """
    pedido = json.loads(body.decode("utf-8"))

    order_id    = pedido.get("order_id", "?")
    customer_id = pedido.get("customer_id", "?")

    # Simula a latência de envio de uma notificação (2–20ms)
    time.sleep(random.uniform(0.002, 0.02))

    # Simula falha de entrega em 1% dos casos (servidor de e-mail fora, etc.)
    if random.random() < 0.01:
        print(f"  [NOTIFICAÇÃO] ❌ FALHA na entrega | Pedido {order_id}")
        ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)
        return

    canal = random.choice(CANAIS)
    print(f"  [NOTIFICAÇÃO] ✅ {canal.upper()} enviado | {order_id} | Cliente {customer_id}")
    ch.basic_ack(delivery_tag=method.delivery_tag)


def main():
    print(f"[NOTIFICAÇÃO] Conectando ao RabbitMQ e ouvindo a fila '{FILA}'...")
    print(f"[NOTIFICAÇÃO] Aguardando pedidos. Pressione Ctrl+C para sair.\n")

    connection = conectar()
    channel = connection.channel()

    # Notificações são rápidas, então aceita mais mensagens por vez (prefetch=20)
    channel.basic_qos(prefetch_count=20)

    channel.basic_consume(
        queue=FILA,
        on_message_callback=processar_notificacao,
        auto_ack=False,
    )

    try:
        channel.start_consuming()
    except KeyboardInterrupt:
        print("\n[NOTIFICAÇÃO] Encerrando...")
        channel.stop_consuming()

    connection.close()


if __name__ == "__main__":
    main()
