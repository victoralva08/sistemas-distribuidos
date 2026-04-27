#!/bin/bash
# quick_start.sh
# ─────────────────────────────────────────────────────────────────────
# Atalho para iniciar tudo de uma vez no Oracle VM
#
# Uso:
#   bash quick_start.sh

set -e

echo ""
echo "╔═══════════════════════════════════════════════════════════════════╗"
echo "║         QUICK START - TP01 RabbitMQ Stress Test Setup            ║"
echo "╚═══════════════════════════════════════════════════════════════════╝"
echo ""

# Step 1: Docker e Swarm
echo "[1/5] Verificando Docker..."
if ! command -v docker &> /dev/null; then
    echo "❌ Docker não encontrado. Instalando..."
    curl -fsSL https://get.docker.com -o get-docker.sh
    sudo sh get-docker.sh
fi

if ! docker info --format='{{.Swarm.LocalNodeState}}' 2>/dev/null | grep -q "active"; then
    echo "▶ Inicializando Docker Swarm..."
    docker swarm init
else
    echo "✓ Docker Swarm já ativo"
fi

# Step 2: Deploy
echo ""
echo "[2/5] Fazendo deploy da stack..."
docker stack deploy -c docker-stack.yml tp01

# Step 3: Aguardar inicialização
echo ""
echo "[3/5] Aguardando services subirem (60s)..."
sleep 60

# Step 4: Cluster RabbitMQ
echo ""
echo "[4/5] Unindo RabbitMQ em cluster..."
bash init_cluster_swarm.sh 2>/dev/null || true

# Step 5: Firewall (Ubuntu/Debian only)
echo ""
echo "[5/5] Configurando firewall..."
if command -v ufw &> /dev/null; then
    echo "▶ Liberando portas (UFW)..."
    sudo ufw allow 5672/tcp 2>/dev/null || true
    sudo ufw allow 5673/tcp 2>/dev/null || true
    sudo ufw allow 5674/tcp 2>/dev/null || true
    sudo ufw allow 15672/tcp 2>/dev/null || true
    sudo ufw allow 5000/tcp 2>/dev/null || true
    sudo ufw allow 5001/tcp 2>/dev/null || true
    sudo ufw enable 2>/dev/null || true
    echo "✓ Firewall configurado"
else
    echo "⚠ UFW não encontrado, pule firewall ou configure manualmente"
fi

# Summary
echo ""
echo "╔═══════════════════════════════════════════════════════════════════╗"
echo "║                    ✅ SETUP CONCLUÍDO!                           ║"
echo "╚═══════════════════════════════════════════════════════════════════╝"
echo ""

# Get IP
IP=$(curl -s ifconfig.me || echo "localhost")

echo "📌 ACESSO DA EQUIPE:"
echo ""
echo "   🔵 API de Pedidos (auto-gera dados):"
echo "   http://$IP:5001/api/order"
echo ""
echo "   📊 Dashboard em Tempo Real:"
echo "   http://$IP:5000"
echo ""
echo "   🐰 RabbitMQ Management UI:"
echo "   http://$IP:15672  (user: admin, pass: admin123)"
echo ""

echo "🚀 EXEMPLOS DE USO DA API:"
echo ""
echo "   # Enviar 1 pedido com dados auto-gerados"
echo "   curl -X POST http://$IP:5001/api/order"
echo ""
echo "   # Enviar 50 pedidos (stress test leve)"
echo "   curl -X POST 'http://$IP:5001/api/order?count=50'"
echo ""
echo "   # Enviar 500 pedidos para fila de estoque"
echo "   curl -X POST 'http://$IP:5001/api/order?count=500&route=stock'"
echo ""
echo "   # Verificar saúde da API"
echo "   curl http://$IP:5001/api/health"
echo ""

echo "📋 PRÓXIMOS PASSOS:"
echo ""
echo "   1. Verificar stack:"
echo "      docker service ls"
echo ""
echo "   2. Escalar consumers (para suportar mais carga):"
echo "      docker service scale tp01_consumer_payment=3"
echo "      docker service scale tp01_consumer_stock=3"
echo "      docker service scale tp01_consumer_notification=5"
echo ""
echo "   3. Ver logs da API:"
echo "      docker service logs tp01_producer_api -f"
echo ""
echo "   4. Monitorar fila via RabbitMQ:"
echo "      docker service logs tp01_rabbit1 -f | grep quorum"
echo ""
echo "   5. Remover tudo:"
echo "      docker stack rm tp01"
echo ""
