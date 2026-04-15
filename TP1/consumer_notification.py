"""
consumer_notification.py – Processa a fila orders.notification.
Simula envio de e-mail / SMS de confirmação de pedido.
"""

import time
import random
from base_consumer import BaseConsumer


class NotificationConsumer(BaseConsumer):
    queue_name   = "orders.notification"
    consumer_tag = "NOTIFY"
    prefetch_count = 20   # notificações são leves, aceita mais de uma vez

    CHANNELS = ["email", "sms", "push"]

    def process(self, payload: dict, ch, method) -> bool:
        order_id    = payload.get("order_id", "?")
        customer_id = payload.get("customer_id", "?")
        event_id    = payload.get("event_id", "")

        # Simula latência de envio (2–20ms)
        time.sleep(random.uniform(0.002, 0.02))

        channel_used = random.choice(self.CHANNELS)

        # Simula falha de entrega em 1% dos casos
        if random.random() < 0.01:
            print(f"  [NOTIFY][FALHA] Notificacao nao entregue | {order_id}")
            return False

        print(f"  [NOTIFY] {channel_used.upper()} enviado | {order_id} | Cliente {customer_id}")
        return True


if __name__ == "__main__":
    NotificationConsumer().run()
