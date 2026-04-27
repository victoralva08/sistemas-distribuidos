# Producer API - Usage Guide

## Overview

The **Producer API** is a REST endpoint that auto-generates realistic order data and publishes it to RabbitMQ. No JSON payload needed—just hit the endpoint with optional query parameters.

## Quick Start

### 1. Start the Stack

```bash
bash quick_start.sh
```

### 2. Test the API

```bash
# Single order
curl -X POST http://localhost:5001/api/order

# 10 orders
curl -X POST 'http://localhost:5001/api/order?count=10'

# 100 orders for stock queue
curl -X POST 'http://localhost:5001/api/order?count=100&route=stock'
```

---

## API Endpoints

### `POST /api/order` — Generate and queue orders

**Auto-generates realistic order data with:**
- Random customer ID (CUST-00001 to CUST-05000)
- Random product (notebook, smartphone, tablet, monitor, headset, keyboard, mouse)
- Random quantity (1-5)
- Random amount ($19.99–$4,999.99)
- ISO timestamp
- Unique event_id and order_id

**Query Parameters:**

| Parameter | Type | Range | Default | Description |
|-----------|------|-------|---------|-------------|
| `count` | int | 1–1000 | 1 | Number of orders to generate |
| `route` | string | `payment`, `stock`, `notification` | random | Queue destination |

**Examples:**

```bash
# 1 order, random route
curl -X POST http://localhost:5001/api/order

# 50 orders, random routes
curl -X POST 'http://localhost:5001/api/order?count=50'

# 100 payment orders
curl -X POST 'http://localhost:5001/api/order?count=100&route=payment'

# 500 stock orders (stress test)
curl -X POST 'http://localhost:5001/api/order?count=500&route=stock'

# 200 notification orders
curl -X POST 'http://localhost:5001/api/order?count=200&route=notification'
```

**Response (201/207):**

```json
{
  "status": "ok",
  "count": 50,
  "sucessos": 50,
  "falhas": 0,
  "orders": [
    {
      "order_id": "ORD-000001",
      "event_id": "550e8400-e29b-41d4-a716-446655440000",
      "success": true
    },
    ...
  ],
  "message": "50/50 pedidos enviados com sucesso"
}
```

---

### `GET /api/health` — Check API and RabbitMQ connection

**Response (200):**

```json
{
  "status": "healthy",
  "rabbitmq": "connected",
  "routes": ["payment", "stock", "notification"],
  "products": ["notebook", "smartphone", "tablet", "monitor", "headset", "keyboard", "mouse"]
}
```

---

### `GET /` — API documentation

Returns full endpoint documentation and available routes/products.

---

## Stress Testing Examples

### Light Load (100 orders)
```bash
curl -X POST 'http://localhost:5001/api/order?count=100'
```

### Medium Load (1000 orders across all queues)
```bash
curl -X POST 'http://localhost:5001/api/order?count=1000'
```

### Heavy Load—Payment Queue (500 sustained)
```bash
for i in {1..10}; do
  curl -X POST 'http://localhost:5001/api/order?count=500&route=payment' &
done
wait
```

### Distributed Load (simulate different services)
```bash
# Terminal 1: Payment processing stress
while true; do
  curl -X POST 'http://localhost:5001/api/order?count=100&route=payment'
  sleep 2
done

# Terminal 2: Stock reserve stress
while true; do
  curl -X POST 'http://localhost:5001/api/order?count=100&route=stock'
  sleep 2
done

# Terminal 3: Notification stress
while true; do
  curl -X POST 'http://localhost:5001/api/order?count=50&route=notification'
  sleep 3
done
```

---

## Monitoring

### Watch Queue Depths
```bash
watch -n 1 'curl -s http://localhost:5001/api/health | jq .'
```

### View Dashboard
```
http://localhost:5000
```
Live topology showing:
- Message counts per queue
- Active consumers
- Publish/deliver rates
- Processing animations

### RabbitMQ Management UI
```
http://localhost:15672
user: admin
pass: admin123
```

---

## Scaling Consumers

As orders flow in, scale consumers to handle the load:

```bash
# Scale payment consumer to 3 replicas
docker service scale tp01_consumer_payment=3

# Scale stock consumer to 5 replicas
docker service scale tp01_consumer_stock=5

# Scale notification consumer to 2 replicas
docker service scale tp01_consumer_notification=2

# View current replicas
docker service ls
```

---

## Troubleshooting

### API returns 503 (RabbitMQ unavailable)
```bash
# Check RabbitMQ service status
docker service ls | grep rabbit

# Check logs
docker service logs tp01_rabbit1 -f
```

### Orders not appearing in queues
```bash
# Check if API is reachable
curl http://localhost:5001/api/health

# Check if messages are being routed
curl http://localhost:15672/api/queues/%2f (RabbitMQ API)
```

### Consumers not processing orders
```bash
# Verify consumer replicas are running
docker service ls | grep consumer

# Check consumer logs
docker service logs tp01_consumer_payment -f
```

---

## Performance Baseline

On a 3-node RabbitMQ cluster with default consumers:

| Scenario | Orders | Time | Throughput | Queue Drain |
|----------|--------|------|-----------|------------|
| Single order | 1 | 50ms | 20 msg/s | instant |
| Light batch | 100 | 500ms | 200 msg/s | <1s |
| Medium batch | 1000 | 3s | 333 msg/s | 5-10s |
| Heavy continuous | 10k | 30s | 333 msg/s | 60-90s |

**Scale up consumers for faster drain. Scale up API replicas for higher POST throughput.**

---

## Cloud Deployment (Oracle VM)

For remote access, replace `localhost` with your Oracle VM IP:

```bash
# Get your public IP
curl ifconfig.me

# Then use in requests
curl -X POST 'http://<ORACLE_VM_IP>:5001/api/order?count=50'
```

**Ensure firewall allows:**
- 5001/tcp (API)
- 5000/tcp (Dashboard)
- 15672/tcp (RabbitMQ UI)
- 5672/tcp (AMQP from queue clients)

See `ORACLE_VM_SETUP.md` for Oracle-specific firewall configuration.
