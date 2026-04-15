"""
consumer_audit.py – Processa a fila orders.audit.
Recebe TODAS as mensagens do sistema (routing key: order.#) e registra
um log completo de auditoria no PostgreSQL.
"""

import json
import time
import random
from base_consumer import BaseConsumer


class AuditConsumer(BaseConsumer):
    queue_name   = "orders.audit"
    consumer_tag = "AUDIT"
    prefetch_count = 50   # audit é leve, aceita lote maior

    def process(self, payload: dict, ch, method) -> bool:
        event_id    = payload.get("event_id", "")
        customer_id = payload.get("customer_id", "?")
        routing_key = method.routing_key

        # Simula gravação rápida de log (1–5ms)
        time.sleep(random.uniform(0.001, 0.005))

        try:
            with self.db.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO audit_log (event_id, customer_id, routing_key, payload)
                    VALUES (%s, %s, %s, %s)
                    """,
                    (event_id, customer_id, routing_key, json.dumps(payload)),
                )
            self.db.commit()
        except Exception as e:
            self.db.rollback()
            print(f"  [AUDIT][DB ERRO] {e}")
            return False

        print(f"  [AUDIT] Registrado | {routing_key} | {payload.get('order_id','?')} | evt={event_id[:8]}...")
        return True


if __name__ == "__main__":
    AuditConsumer().run()
