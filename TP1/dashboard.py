"""
dashboard.py
------------
PAINEL DE MONITORAMENTO

Este script é um servidor web simples (Flask) que exibe o painel visual.
Ele consulta a API de gerenciamento do RabbitMQ a cada segundo e envia
os dados para o navegador usando SSE (Server-Sent Events).

O que é SSE?
  É uma tecnologia que mantém a conexão HTTP aberta e deixa o servidor
  "empurrar" atualizações para o navegador automaticamente, sem o navegador
  precisar ficar fazendo refresh ou pedindo dados (polling).

Como executar:
  python dashboard.py

Depois, abra no navegador:
  http://localhost:5000
"""

from flask import Flask, Response, render_template
import requests
import json
import time

app = Flask(__name__)

# URL da API de gerenciamento interna do RabbitMQ (Management Plugin)
RABBITMQ_API_OVERVIEW = "http://localhost:15672/api/overview"
RABBITMQ_API_QUEUES = "http://localhost:15672/api/queues"
AUTH = ("admin", "admin123")


@app.route("/")
def index():
    """Serve a página principal do dashboard."""
    return render_template("index.html")


def buscar_metricas():
    """
    Consulta a API do RabbitMQ e retorna os dados das filas e taxas globais.
    """
    try:
        # Pega as filas
        res_queues = requests.get(RABBITMQ_API_QUEUES, auth=AUTH, timeout=2)
        res_queues.raise_for_status()
        filas = res_queues.json()

        # Pega as taxas (publish / deliver globais)
        res_overview = requests.get(RABBITMQ_API_OVERVIEW, auth=AUTH, timeout=2)
        res_overview.raise_for_status()
        overview = res_overview.json()
        stats = overview.get("message_stats", {})

        dados_filas = {}
        for fila in filas:
            nome = fila.get("name")
            dados_filas[nome] = {
                "messages": fila.get("messages_ready", 0),
                "consumers": fila.get("consumers", 0),
                "acked": fila.get("message_stats", {}).get("ack", 0) if isinstance(fila.get("message_stats"), dict) else 0
            }

        return {
            "status": "ok",
            "publish_rate": stats.get("publish_details", {}).get("rate", 0.0),
            "deliver_rate": stats.get("deliver_get_details", {}).get("rate", 0.0),
            "queues": dados_filas
        }
    except Exception as e:
        return {"error": str(e)}


@app.route("/stream")
def stream():
    """
    Endpoint SSE: mantém a conexão aberta e envia métricas a cada 1 segundo.
    O navegador se conecta uma vez e fica recebendo atualizações automaticamente.
    """
    def gerador_eventos():
        while True:
            metricas = buscar_metricas()
            # Formato SSE: cada evento começa com "data: " e termina com "\n\n"
            yield f"data: {json.dumps(metricas)}\n\n"
            time.sleep(1)

    return Response(gerador_eventos(), content_type="text/event-stream")


if __name__ == "__main__":
    print("Dashboard iniciado! Acesse: http://localhost:5000")
    app.run(host="0.0.0.0", port=5000, debug=True)
