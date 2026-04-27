"""
producer_api.py
---------------
API REST para enviar pedidos para a fila do RabbitMQ.

Pessoas no mundo podem fazer requisições simples e os pedidos são auto-gerados.

Como executar:
  python producer_api.py

Exemplos de requisição:
  # Submete 1 pedido com dados aleatórios
  curl -X POST http://localhost:5000/api/order

  # Submete 10 pedidos em paralelo
  curl -X POST http://localhost:5000/api/order?count=10

  # Especifica a rota (payment, stock, notification)
  curl -X POST http://localhost:5000/api/order?route=stock

  # Combina: 50 pedidos para estoque
  curl -X POST http://localhost:5000/api/order?count=50&route=stock
"""

import pika
import uuid
import json
import os
import random
import threading
from datetime import datetime, timezone
from flask import Flask, request, jsonify

app = Flask(__name__)

# ── Configurações via environment variables ────────────────────────
RABBITMQ_HOST = os.getenv("RABBITMQ_HOST", "localhost")
RABBITMQ_USER = os.getenv("RABBITMQ_USER", "admin")
RABBITMQ_PASS = os.getenv("RABBITMQ_PASS", "admin123")
EXCHANGE_NAME = "orders.exchange"

# Produtos e rotas disponíveis
PRODUCTS = ["notebook", "smartphone", "tablet", "monitor", "headset", "keyboard", "mouse"]
ROUTING_KEYS = {
    "payment": "order.payment.new",
    "stock": "order.stock.reserve",
    "notification": "order.notify.confirm",
}


def conectar():
    """Abre conexão com RabbitMQ."""
    credentials = pika.PlainCredentials(RABBITMQ_USER, RABBITMQ_PASS)
    params = pika.ConnectionParameters(
        host=RABBITMQ_HOST,
        credentials=credentials,
        heartbeat=600,
        blocked_connection_timeout=300,
    )
    return pika.BlockingConnection(params)


def gerar_pedido(numero: int) -> dict:
    """Gera um pedido fictício com dados aleatórios."""
    return {
        "event_id": str(uuid.uuid4()),
        "order_id": f"ORD-{numero:06d}",
        "customer_id": f"CUST-{random.randint(1, 5000):05d}",
        "product_id": random.choice(PRODUCTS),
        "quantity": random.randint(1, 5),
        "amount": round(random.uniform(19.99, 4999.99), 2),
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


def publicar_pedido(pedido: dict, routing_key: str) -> dict:
    """Publica um pedido para o RabbitMQ. Retorna resultado da operação."""
    try:
        connection = conectar()
        channel = connection.channel()
        channel.confirm_delivery()
        
        corpo = json.dumps(pedido).encode("utf-8")
        channel.basic_publish(
            exchange=EXCHANGE_NAME,
            routing_key=routing_key,
            body=corpo,
            properties=pika.BasicProperties(
                delivery_mode=2,
                content_type="application/json",
                message_id=pedido["event_id"],
            ),
            mandatory=True,
        )
        connection.close()
        
        return {
            "success": True,
            "order_id": pedido["order_id"],
            "event_id": pedido["event_id"],
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
        }


@app.route("/api/order", methods=["POST"])
def submit_order():
    """
    Endpoint para submissions remotas de pedidos com geração automática.
    
    Query parameters (opcionais):
      - count: número de pedidos a gerar (padrão: 1)
      - route: tipo de rota - payment|stock|notification (padrão: aleatório)
    
    Exemplos:
      POST /api/order                          → 1 pedido com rota aleatória
      POST /api/order?count=10                 → 10 pedidos com rota aleatória
      POST /api/order?count=50&route=stock     → 50 pedidos para a fila de estoque
    
    Response:
    {
      "status": "ok",
      "count": 10,
      "orders": [
        {"order_id": "ORD-000001", "event_id": "uuid-...", "success": true},
        ...
      ],
      "message": "10 pedidos enviados com sucesso"
    }
    """
    try:
        # Parse query parameters
        count = request.args.get("count", default=1, type=int)
        route = request.args.get("route", default=None, type=str)
        
        # Validações
        if count < 1 or count > 1000:
            return jsonify({
                "status": "error",
                "message": "count deve estar entre 1 e 1000"
            }), 400
        
        if route and route not in ROUTING_KEYS:
            return jsonify({
                "status": "error",
                "message": f"route inválida. Válidas: {list(ROUTING_KEYS.keys())}"
            }), 400
        
        # Função para publicar um pedido individual
        def enviar_em_thread(numero: int, pedido: dict, routing_key: str):
            resultados[numero] = publicar_pedido(pedido, routing_key)
        
        resultados = {}
        threads = []
        
        for i in range(1, count + 1):
            # Gera pedido com dados aleatórios
            pedido = gerar_pedido(i)
            
            # Escolhe rota: força a especificada ou escolhe aleatoriamente
            if route:
                routing_key = ROUTING_KEYS[route]
            else:
                routing_key = random.choice(list(ROUTING_KEYS.values()))
            
            # Publica em thread separada para paralelismo
            t = threading.Thread(
                target=enviar_em_thread,
                args=(i, pedido, routing_key),
                daemon=True
            )
            threads.append(t)
            t.start()
        
        # Aguarda todas as threads terminarem
        for t in threads:
            t.join(timeout=10)
        
        # Coleta resultados
        sucessos = sum(1 for r in resultados.values() if r.get("success"))
        falhas = count - sucessos
        
        return jsonify({
            "status": "ok" if falhas == 0 else "partial",
            "count": count,
            "sucessos": sucessos,
            "falhas": falhas,
            "orders": list(resultados.values()),
            "message": f"{sucessos}/{count} pedidos enviados com sucesso"
        }), 201 if falhas == 0 else 207
    
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": f"Erro interno: {str(e)}"
        }), 500


@app.route("/api/health", methods=["GET"])
def health():
    """Health check endpoint."""
    try:
        connection = conectar()
        channel = connection.channel()
        connection.close()
        return jsonify({
            "status": "healthy",
            "rabbitmq": "connected",
            "routes": list(ROUTING_KEYS.keys()),
            "products": PRODUCTS
        }), 200
    except Exception as e:
        return jsonify({
            "status": "unhealthy",
            "rabbitmq": "disconnected",
            "error": str(e)
        }), 503


@app.route("/", methods=["GET"])
def index():
    """Informações e documentação da API."""
    return jsonify({
        "service": "Producer API - TP01",
        "version": "2.0",
        "description": "API para enviar pedidos automaticamente gerados para fila RabbitMQ",
        "endpoints": {
            "POST /api/order": {
                "description": "Submete pedidos com dados auto-gerados",
                "params": {
                    "count": "número de pedidos (1-1000, padrão 1)",
                    "route": "tipo de rota - payment|stock|notification (padrão: aleatório)"
                },
                "examples": [
                    "POST /api/order",
                    "POST /api/order?count=10",
                    "POST /api/order?count=50&route=stock"
                ]
            },
            "GET /api/health": "Verifica saúde da API e conexão com RabbitMQ",
            "GET /": "Esta mensagem"
        },
        "available_routes": ROUTING_KEYS,
        "available_products": PRODUCTS
    }), 200


if __name__ == "__main__":
    print(f"[API] Iniciando Producer API...")
    print(f"[API] Conectando ao RabbitMQ em {RABBITMQ_HOST}...")
    print(f"[API] Servidor rodando em http://0.0.0.0:5000")
    print(f"[API] Acesse http://0.0.0.0:5000 para documentação")
    app.run(host="0.0.0.0", port=5000, debug=False)
