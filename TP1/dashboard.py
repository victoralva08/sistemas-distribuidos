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
RABBITMQ_API = "http://localhost:15672/api/overview"
AUTH = ("admin", "admin123")


@app.route("/")
def index():
    """Serve a página principal do dashboard."""
    return render_template("index.html")


def buscar_metricas():
    """
    Consulta a API do RabbitMQ e retorna as métricas mais importantes
    em um dicionário simples.
    Se o RabbitMQ estiver offline, retorna um dicionário com chave 'error'.
    """
    try:
        resposta = requests.get(RABBITMQ_API, auth=AUTH, timeout=2)
        resposta.raise_for_status()
        dados = resposta.json()

        estatisticas_msgs = dados.get("message_stats", {})
        totais_filas      = dados.get("queue_totals", {})
        totais_objetos    = dados.get("object_totals", {})

        return {
            # Velocidade de entrada (mensagens publicadas por segundo)
            "publish_rate": estatisticas_msgs.get("publish_details", {}).get("rate", 0.0),
            # Velocidade de saída (mensagens entregues aos consumers por segundo)
            "deliver_rate": estatisticas_msgs.get("deliver_get_details", {}).get("rate", 0.0),
            # Mensagens aguardando para serem consumidas
            "messages_ready": totais_filas.get("messages_ready", 0),
            # Mensagens que saíram da fila mas ainda não foram confirmadas pelo consumer
            "messages_unacked": totais_filas.get("messages_unacknowledged", 0),
            # Quantidade de conexões AMQP abertas
            "connections": totais_objetos.get("connections", 0),
            # Quantidade de consumers ativos em todas as filas
            "consumers": totais_objetos.get("consumers", 0),
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
