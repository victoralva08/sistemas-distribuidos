"""
consumer_payment.py – Processa a fila orders.payment.
Simula validação e cobrança de pagamento, salvando no PostgreSQL.
"""

import time
import random
from base_consumer import BaseConsumer


class PaymentConsumer(BaseConsumer):
    queue_name   = "orders.payment"
    consumer_tag = "PAYMENT"
    prefetch_count = 10

    def process(self, payload: dict, ch, method) -> bool:
        order_id    = payload.get("order_id", "?")
        customer_id = payload.get("customer_id", "?")
        amount      = payload.get("amount", 0.0)
        event_id    = payload.get("event_id", "")

        # Simula tempo de processamento do pagamento (5–50ms)
        time.sleep(random.uniform(0.005, 0.05))

        # Simula falha em 2% dos casos (vai para DLQ)
        if random.random() < 0.02:
            print(f"  [PAYMENT][FALHA] Pedido {order_id} recusado (simulado)")
            return False

        # Persiste no PostgreSQL
        try:
            with self.db.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO payments (event_id, customer_id, amount, status)
                    VALUES (%s, %s, %s, 'approved')
                    """,
                    (event_id, customer_id, amount),
                )
            self.db.commit()
        except Exception as e:
            self.db.rollback()
            print(f"  [PAYMENT][DB ERRO] {e}")
            return False

        print(f"  [PAYMENT] Aprovado | {order_id} | R$ {amount:.2f} | Cliente {customer_id}")
        return True


if __name__ == "__main__":
    PaymentConsumer().run()
