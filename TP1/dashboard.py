import os
from flask import Flask, Response, render_template
import requests
import json
import time

app = Flask(__name__)

RABBIT_URL = "http://localhost:15672/api/overview"
AUTH = ("admin", "admin123")

@app.route("/")
def index():
    return render_template("index.html")

def get_rabbitmq_metrics():
    try:
        r = requests.get(RABBIT_URL, auth=AUTH, timeout=2)
        r.raise_for_status()
        data = r.json()
        
        msg_stats = data.get("message_stats", {})
        queue_totals = data.get("queue_totals", {})
        obj_totals = data.get("object_totals", {})
        
        return {
            "publish_rate": msg_stats.get("publish_details", {}).get("rate", 0.0),
            "deliver_rate": msg_stats.get("deliver_get_details", {}).get("rate", 0.0),
            "messages_ready": queue_totals.get("messages_ready", 0),
            "messages_unacked": queue_totals.get("messages_unacknowledged", 0),
            "connections": obj_totals.get("connections", 0),
            "consumers": obj_totals.get("consumers", 0)
        }
    except Exception as e:
        return {"error": str(e)}

@app.route("/stream")
def stream():
    def event_stream():
        while True:
            metrics = get_rabbitmq_metrics()
            yield f"data: {json.dumps(metrics)}\n\n"
            time.sleep(1)
    
    return Response(event_stream(), content_type="text/event-stream")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
