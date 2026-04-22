"""
consumer_payment.py
-------------------
CONSUMIDOR DE PAGAMENTO

Este script fica "escutando" a fila orders.payment esperando pedidos chegarem.
Quando um pedido chega, ele simula a validação e cobrança do pagamento.

Como funciona:
  1. Conecta ao RabbitMQ
  2. Se registra na fila orders.payment
  3. Para cada pedido recebido, valida e decide se aprova ou rejeita
  4. Envia ACK (confirmação) se aprovado, ou NACK (rejeição) se recusado
     → Mensagens recusadas vão automaticamente para a Dead Letter Queue (DLQ)

Execute com:
  python consumer_payment.py
"""

import pika
import json
import time
import random

# ── Configurações ──────────────────────────────────────────────────
RABBITMQ_HOST = "localhost"
RABBITMQ_USER = "admin"
RABBITMQ_PASS = "admin123"
FILA = "orders.payment"


def conectar():
    """Abre e retorna uma conexão com o RabbitMQ."""
    credentials = pika.PlainCredentials(RABBITMQ_USER, RABBITMQ_PASS)
    params = pika.ConnectionParameters(
        host=RABBITMQ_HOST,
        credentials=credentials,
        heartbeat=600,
    )
    return pika.BlockingConnection(params)


def processar_pagamento(ch, method, properties, body):
    """
    Função chamada automaticamente pelo RabbitMQ a cada mensagem recebida.
    Parâmetros:
      ch         → canal de comunicação (usado para confirmar/rejeitar)
      method     → metadados da entrega (contém delivery_tag para o ACK)
      properties → cabeçalhos da mensagem (não usamos aqui)
      body       → conteúdo da mensagem em bytes
    """
    pedido = json.loads(body.decode("utf-8"))

    order_id    = pedido.get("order_id", "?")
    customer_id = pedido.get("customer_id", "?")
    amount      = pedido.get("amount", 0.0)

    # Simula o tempo que um sistema real de pagamento levaria (5–50ms)
    time.sleep(random.uniform(0.005, 0.05))

    print(f"  [PAGAMENTO] ✅ Aprovado | {order_id} | R$ {amount:.2f} | Cliente {customer_id}")
    # Confirma que a mensagem foi processada com sucesso
    ch.basic_ack(delivery_tag=method.delivery_tag)


def main():
    print(f"[PAGAMENTO] Conectando ao RabbitMQ e ouvindo a fila '{FILA}'...")
    print(f"[PAGAMENTO] Aguardando pedidos. Pressione Ctrl+C para sair.\n")

    connection = conectar()
    channel = connection.channel()

    # prefetch_count=10 → recebe no máximo 10 mensagens de uma vez,
    # evitando sobrecarregar este consumidor enquanto outros ficam sem trabalho
    channel.basic_qos(prefetch_count=10)

    channel.basic_consume(
        queue=FILA,
        on_message_callback=processar_pagamento,
        auto_ack=False,  # False = o script confirma manualmente (mais seguro)
    )

    try:
        channel.start_consuming()
    except KeyboardInterrupt:
        print("\n[PAGAMENTO] Encerrando...")
        channel.stop_consuming()

    connection.close()


if __name__ == "__main__":
    main()
