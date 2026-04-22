"""
consumer_audit.py
-----------------
CONSUMIDOR DE AUDITORIA

Este script é especial: ele escuta TODAS as mensagens do sistema,
independente do tipo (pagamento, estoque, notificação).

Isso é possível porque a fila orders.audit usa a routing key "order.#",
onde o "#" é um curinga que significa "qualquer coisa depois de order.".

Seu papel é registrar um log de tudo o que acontece no sistema,
funcionando como uma "caixa preta" do e-commerce.

Execute com:
  python consumer_audit.py
"""

import pika
import json
import time
import random
from datetime import datetime

# ── Configurações ──────────────────────────────────────────────────
RABBITMQ_HOST = "localhost"
RABBITMQ_USER = "admin"
RABBITMQ_PASS = "admin123"
FILA = "orders.audit"


def conectar():
    """Abre e retorna uma conexão com o RabbitMQ."""
    credentials = pika.PlainCredentials(RABBITMQ_USER, RABBITMQ_PASS)
    params = pika.ConnectionParameters(
        host=RABBITMQ_HOST,
        credentials=credentials,
        heartbeat=600,
    )
    return pika.BlockingConnection(params)


def processar_auditoria(ch, method, properties, body):
    """
    Função chamada automaticamente pelo RabbitMQ a cada mensagem recebida.
    Registra no terminal um log completo do evento recebido.
    Em um sistema real, isso seria gravado em arquivo ou banco de dados de auditoria.
    """
    pedido = json.loads(body.decode("utf-8"))

    event_id    = pedido.get("event_id", "")
    order_id    = pedido.get("order_id", "?")
    customer_id = pedido.get("customer_id", "?")
    routing_key = method.routing_key  # ex: "order.payment.new"

    # Simula o tempo de gravação do log (1–5ms, bem rápido)
    time.sleep(random.uniform(0.001, 0.005))

    agora = datetime.now().strftime("%H:%M:%S")
    print(f"  [AUDITORIA] 📋 {agora} | {routing_key} | {order_id} | "
          f"Cliente {customer_id} | evt={event_id[:8]}...")

    ch.basic_ack(delivery_tag=method.delivery_tag)


def main():
    print(f"[AUDITORIA] Conectando ao RabbitMQ e ouvindo a fila '{FILA}'...")
    print(f"[AUDITORIA] Registrando TODOS os eventos do sistema. Ctrl+C para sair.\n")

    connection = conectar()
    channel = connection.channel()

    # Auditoria é muito rápida, então aceita lotes maiores (prefetch=50)
    channel.basic_qos(prefetch_count=50)

    channel.basic_consume(
        queue=FILA,
        on_message_callback=processar_auditoria,
        auto_ack=False,
    )

    try:
        channel.start_consuming()
    except KeyboardInterrupt:
        print("\n[AUDITORIA] Encerrando...")
        channel.stop_consuming()

    connection.close()


if __name__ == "__main__":
    main()
