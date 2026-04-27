# TP1_Core - Minimal RabbitMQ Queue Implementation

The **simplest possible** distributed queue system with RabbitMQ.

---

## What's Included

- **docker-compose.yml** — Single RabbitMQ node (no cluster)
- **producer.py** — Sends 100 messages (configurable)
- **consumer_payment.py** — Processes payment queue
- **consumer_stock.py** — Processes stock queue
- **consumer_notification.py** — Processes notification queue

---

## Quick Start (5 minutes)

### Step 1: Start RabbitMQ

```bash
docker compose up -d
```

Verify it's running:
```bash
docker ps
# Should show: rabbitmq:3.13-management
```

Access RabbitMQ UI: http://localhost:15672 (admin/admin123)

---

### Step 2: Install Python Dependencies

```bash
pip install -r requirements.txt
```

---

### Step 3: Open 4 Terminals

**Terminal 1—Producer (sends messages):**
```bash
python producer.py 100
# Sends 100 messages to RabbitMQ
```

**Terminal 2—Payment Consumer:**
```bash
python consumer_payment.py
# Listens and processes messages
```

**Terminal 3—Stock Consumer:**
```bash
python consumer_stock.py
# Listens and processes messages
```

**Terminal 4—Notification Consumer:**
```bash
python consumer_notification.py
# Listens and processes messages
```

---

## How It Works

```
Producer
   ↓
RabbitMQ Exchange (fanout)
   ↓
├→ orders.payment ──→ consumer_payment.py
├→ orders.stock ────→ consumer_stock.py
└→ orders.notification ──→ consumer_notification.py
```

All consumers receive **every message** (fanout pattern).

---

## Test Different Loads

```bash
python producer.py 10      # 10 messages
python producer.py 1000    # 1000 messages
python producer.py 10000   # 10000 messages
```

Consumers will process in real-time and print progress.

---

## Verify Messages in RabbitMQ UI

1. Go to http://localhost:15672
2. Login: admin / admin123
3. Go to **Queues** tab
4. You'll see:
   - `orders.payment`
   - `orders.stock`
   - `orders.notification`

Click a queue to see messages, inspect content, etc.

---

## Stop Everything

```bash
# Stop consumers (Ctrl+C in each terminal)

# Stop RabbitMQ
docker compose down
```

---

## Code Structure

| File | Purpose |
|------|---------|
| `producer.py` | Generates random order data, sends to queue |
| `consumer_payment.py` | Listens & processes (prints order) |
| `consumer_stock.py` | Listens & processes (prints order) |
| `consumer_notification.py` | Listens & processes (prints order) |
| `docker-compose.yml` | Single RabbitMQ container |
| `requirements.txt` | Python dependencies |

---

## Troubleshooting

### "Connection refused"
```bash
# Check if Docker container is running
docker ps

# If not, start it
docker compose up -d
```

### "Module pika not found"
```bash
# Install dependencies
pip install -r requirements.txt
```

### See what's in queues
```bash
# In RabbitMQ UI
http://localhost:15672 → Queues
```

### Clear all queues
```bash
docker compose down -v
docker compose up -d
```

---

## Next Steps

Want to make it more complex?
- Add retry logic (NACK)
- Add multiple consumers per queue (load balancing)
- Add persistence to database
- Add monitoring/metrics
- Containerize the Python scripts

For **production-ready version**, see `../TP1/` with API, dashboard, clustering, Swarm, etc.

---

That's it! Pure, minimal, core functionality. 🚀
