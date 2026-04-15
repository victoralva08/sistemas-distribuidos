"""
consumer_stock.py – Processa a fila orders.stock.
Simula reserva de estoque, salvando no PostgreSQL.
"""

import time
import random
from base_consumer import BaseConsumer


class StockConsumer(BaseConsumer):
    queue_name   = "orders.stock"
    consumer_tag = "STOCK"
    prefetch_count = 10

    def process(self, payload: dict, ch, method) -> bool:
        order_id    = payload.get("order_id", "?")
        customer_id = payload.get("customer_id", "?")
        product_id  = payload.get("product_id", "?")
        quantity    = payload.get("quantity", 1)
        event_id    = payload.get("event_id", "")

        # Simula consulta ao estoque (10–30ms)
        time.sleep(random.uniform(0.01, 0.03))

        # Simula falta de estoque em 3% dos casos
        if random.random() < 0.03:
            print(f"  [STOCK][SEM ESTOQUE] {product_id} | Pedido {order_id}")
            return False

        try:
            with self.db.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO inventory (event_id, customer_id, product_id, quantity, status)
                    VALUES (%s, %s, %s, %s, 'reserved')
                    """,
                    (event_id, customer_id, product_id, quantity),
                )
            self.db.commit()
        except Exception as e:
            self.db.rollback()
            print(f"  [STOCK][DB ERRO] {e}")
            return False

        print(f"  [STOCK] Reservado | {order_id} | {quantity}x {product_id} | Cliente {customer_id}")
        return True


if __name__ == "__main__":
    StockConsumer().run()
