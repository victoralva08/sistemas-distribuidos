"""
=================================================================
             IMPLEMENTAÇÃO CONCLUÍDA - API AUTO-GERADA
=================================================================

Você agora tem um ambiente pronto para deploy em cloud (Oracle VM)
com suporte a acesso remoto via API REST COM AUTO-GERAÇÃO DE DADOS.

## O QUE FOI CRIADO

### 1. NOVO SERVIÇO: producer_api.py ✅ (AUTO-GERA DADOS)
   
   ❌ NÃO PRECISA mais enviar JSON no corpo
   ✅ BASTA fazer: curl -X POST http://ORACLE_VM_IP:5001/api/order
   
   Features:
   - Flask REST API na porta 5001
   - Endpoint POST /api/order com auto-geração de dados
   - Query params: count (1-1000), route (payment|stock|notification)
   - Auto-gera: customer_id, product_id, quantity, amount, timestamp
   - Health check GET /api/health
   - Documentação em GET /
   - Publicação paralela (threading) para throughput
   - Incluso no docker-stack.yml

   Exemplos de uso:
   
   # 1 pedido aleatório
   curl -X POST http://ORACLE_VM_IP:5001/api/order
   
   # 50 pedidos aleatórios
   curl -X POST 'http://ORACLE_VM_IP:5001/api/order?count=50'
   
   # 500 pedidos para fila de estoque
   curl -X POST 'http://ORACLE_VM_IP:5001/api/order?count=500&route=stock'
   
   # 200 pedidos para fila de pagamento
   curl -X POST 'http://ORACLE_VM_IP:5001/api/order?count=200&route=payment'

### 2. ATUALIZADO: docker-stack.yml ✅
   
   Serviços inclusos:
   
   a) RabbitMQ Cluster (3 nós)
      - rabbit1/rabbit2/rabbit3 com replicação Quorum
      - Portas 5672-5674 (AMQP)
      - UI de gerenciamento na 15672
   
   b) producer_api (1 instância, escalável)
      - REST API para submeter pedidos (auto-gera dados)
      - Porta 5001 (externa)
      - Lê: RABBITMQ_HOST, RABBITMQ_USER, RABBITMQ_PASS
   
   c) dashboard (1 instância)
      - Monitoramento em tempo real com SSE
      - Visualização de topologia interativa
      - Porta 5000 (externa)
   
   d) consumer_payment (1 instância, scale para 3-10)
      - Processa fila orders.payment
      - QoS prefetch: 10
   
   e) consumer_stock (1 instância, scale para 3-10)
      - Processa fila orders.stock
      - QoS prefetch: 10
   
   f) consumer_notification (1 instância, scale para 2-5)
      - Processa fila orders.notification
      - QoS prefetch: 20 (mais rápido)

### 3. NOVO: API_USAGE.md ✅
   
   Documentação completa:
   - Referência de endpoints
   - Parâmetros explicados
   - Exemplos de uso (leve, médio, pesado)
   - Cenários de stress test
   - Baselines de performance
   - Guide de troubleshooting

### 4. ATUALIZADO: ORACLE_VM_SETUP.md ✅
   
   Configuração completa:
   - Oracle Cloud security groups
   - UFW firewall rules (recomendado)
   - Deploy passo-a-passo
   - Teste de acesso remoto
   - Monitoramento em tempo real
   - Dicas de segurança para produção

### 5. ATUALIZADO: quick_start.sh ✅
   
   Deployment automático:
   - 1 comando: bash quick_start.sh
   - Valida Docker e Swarm
   - Deploy da stack
   - Configuração de firewall (UFW)
   - Saída com URLs de acesso para a equipe
   - Exemplos de uso da API

### 6. ATUALIZADO: Todos os Python scripts ✅
   
   Agora leem environment variables:
   - producer.py
   - consumer_payment.py
   - consumer_stock.py
   - consumer_notification.py
   - dashboard.py
   
   Variáveis:
   - RABBITMQ_HOST (default: localhost)
   - RABBITMQ_USER (default: admin)
   - RABBITMQ_PASS (default: admin123)

## ARQUITETURA

```
┌─ Docker Swarm (Oracle VM) ──────────────────────────┐
│                                                      │
│  🐰 RabbitMQ Cluster (3 nós, replicado)            │
│     ├─ rabbit1:5672 (AMQP)                         │
│     ├─ rabbit2:5673                                │
│     ├─ rabbit3:5674                                │
│     └─ UI Management: 15672                        │
│                                                     │
│  🔵 Producer API (porta 5001)                      │
│     Auto-gera dados → RabbitMQ                    │
│     /api/order?count=X&route=Y                    │
│                                                     │
│  📊 Dashboard (porta 5000)                         │
│     Topologia em tempo real via SSE                │
│     Monitor filas, consumers, taxas                │
│                                                     │
│  ⭐ Consumers (auto-escaláveis)                    │
│     ├─ payment (1-10 replicas)                    │
│     ├─ stock (1-10 replicas)                      │
│     └─ notification (1-10 replicas)               │
│                                                     │
└──────────────────────────────────────────────────── ┘
```

## COMO USAR

### Local (desenvolvimento)

```bash
bash quick_start.sh

# API
curl -X POST 'http://localhost:5001/api/order?count=50'

# Dashboard
open http://localhost:5000

# RabbitMQ UI
open http://localhost:15672
```

### Oracle VM (produção/cloud)

```bash
ssh ubuntu@<IP>
git clone <repo>
cd TP1
bash quick_start.sh

# Após deploy:
# API: http://<IP>:5001/api/order
# Dashboard: http://<IP>:5000
# RabbitMQ UI: http://<IP>:15672
```

## SCALE HORIZONTAL

```bash
# Aumentar consumers conforme carga
docker service scale tp01_consumer_payment=5
docker service scale tp01_consumer_stock=10
docker service scale tp01_consumer_notification=3

# Ver status
docker service ls
```

## FIREWALL (Oracle Cloud + UFW)

```bash
# Regras no console OCI (Security Lists)
Port 5001 - TCP - 0.0.0.0/0  (API)
Port 5000 - TCP - 0.0.0.0/0  (Dashboard)
Port 15672 - TCP - 0.0.0.0/0 (RabbitMQ UI)

# Ou na VM:
sudo ufw allow 5001/tcp
sudo ufw allow 5000/tcp
sudo ufw allow 15672/tcp
sudo ufw enable
```

## PRÓXIMOS PASSOS

1. Deploy em Oracle VM (veja ORACLE_VM_SETUP.md)
2. Compartilhar URLs com a equipe
3. Monitorar via dashboard http://<IP>:5000
4. Escalar consumers conforme necessário
5. Documentar resultados dos testes


   d) consumer_stock (1 instância, escalável)
      - Processa fila orders.stock
      - Simula reserva de estoque

   e) consumer_notification (1 instância, escalável)
      - Processa fila orders.notification
      - Simula envio de notificação

   Todos com:
   - Variáveis de ambiente para hostname RabbitMQ
   - Restart policy automática
   - Network overlay para comunicação entre VMs

### 4. ATUALIZADO: Todos os Scripts Python ✅
   producer.py
   consumer_payment.py
   consumer_stock.py
   consumer_notification.py
   dashboard.py

   Mudança: Adicionado suporte a environment variables
   - RABBITMQ_HOST (padrão: localhost)
   - RABBITMQ_USER (padrão: admin)
   - RABBITMQ_PASS (padrão: admin123)

   Benefício: Scripts funcionam tanto localmente quanto em cloud
   sem precisar editar código.

### 5. NOVO GUIA: CLOUD_DEPLOYMENT.md ✅
   Instruções passo a passo para:
   - Iniciar Swarm e deploy
   - Usar API REST
   - Monitorar dashboard
   - Escalar consumers
   - Stress test
   - Troubleshooting

### 6. NOVO GUIA: ORACLE_VM_SETUP.md ✅
   Configuração de rede no Oracle VM:
   - Firewall rules (UFW, iptables)
   - Oracle Cloud Security Groups
   - Como obter IP público
   - SSL/TLS opcional
   - VPN
   - Resumo rápido

---

## ARQUITETURA ATUAL

┌─────────────────────────────────────────────────────────┐
│                   ORACLE VM (Internet)                   │
│                                                          │
│  Docker Swarm Manager (1 máquina)                       │
│  ┌────────────────────────────────────────┐            │
│  │ RabbitMQ Cluster (3 nós)               │            │
│  │  ├─ rabbit1 (manager)                  │            │
│  │  ├─ rabbit2                            │            │
│  │  └─ rabbit3                            │            │
│  │                                        │            │
│  │ App Services (escaláveis)              │            │
│  │  ├─ producer_api (1)      → porta 5000 │ ← Remote
│  │  ├─ dashboard (1)         → porta 5001 │   Acesso
│  │  ├─ consumer_payment (1)  [escala 5+] │
│  │  ├─ consumer_stock (1)    [escala 5+] │
│  │  └─ consumer_notification (1) [5+]    │
│  │                                        │
│  │ Rede Overlay (docker_network)          │
│  └────────────────────────────────────────┘
│
│ Portas Abertas:
│  - 5672, 5673, 5674  → AMQP (RabbitMQ protocol)
│  - 15672             → RabbitMQ Management UI
│  - 5000              → Producer API (seu uso principal)
│  - 5001              → Dashboard
│
└─────────────────────────────────────────────────────────┘

---

## FLUXO DE DADOS

1. PESSOA ENVIA PEDIDO
   POST http://ORACLE_VM_IP:5000/api/order
        ↓
   producer_api valida dados
        ↓
   producer_api publica em orders.exchange (RabbitMQ)
        ↓
2. RABBITMQ ROTEIA
   exchange distribui para:
   - orders.payment      (se routing_key = order.payment.*)
   - orders.stock        (se routing_key = order.stock.*)
   - orders.notification (se routing_key = order.notify.*)
        ↓
3. CONSUMERS PROCESSAM
   - consumer_payment      processa orders.payment
   - consumer_stock        processa orders.stock
   - consumer_notification processa orders.notification
        ↓
4. PESSOA MONITORA
   GET http://ORACLE_VM_IP:5001 (dashboard SSE)
        ↓
   Dashboard consulta RabbitMQ API em tempo real
        ↓
   Mostra fila profundidade, consumers conectados, msgs/s

---

## COMO COMEÇAR NO ORACLE VM

1. SSH into Oracle VM:
   ssh user@<ORACLE_VM_IP>

2. Clone ou copie TP1:
   cd ~
   mkdir -p projetos
   # copie os arquivos TP1 aqui

3. Iniciar Swarm:
   docker swarm init

4. Deploy:
   cd ~/projetos/TP1
   docker stack deploy -c docker-stack.yml tp01

5. Aguarde ~60s e cluster:
   bash init_cluster_swarm.sh

6. Liberar firewall:
   sudo ufw allow 5672/tcp
   sudo ufw allow 15672/tcp
   sudo ufw allow 5000/tcp
   sudo ufw allow 5001/tcp
   sudo ufw enable

7. Obter IP:
   curl ifconfig.me

8. Compartilhar:
   "Enviem pedidos para: http://<IP>:5000/api/order
    Monitorem em: http://<IP>:5001
    RabbitMQ UI: http://<IP>:15672"

---

## SCALING PARA STRESS TEST

Producer API é threadable (concurrent requests), mas RabbitMQ é o gargalo.
Para aumentar throughput:

1. Aumentar consumers:
   docker service scale tp01_consumer_payment=10
   docker service scale tp01_consumer_stock=10
   docker service scale tp01_consumer_notification=10

2. Aumentar produção:
   # Localmente (sua máquina)
   python3 load_generator.py --target http://ORACLE_VM_IP:5000/api/order \
                             --total 10000 \
                             --concurrency 50

3. Monitorar:
   - Dashboard: http://ORACLE_VM_IP:5001
   - Logs: docker service logs tp01_consumer_payment
   - RabbitMQ UI: http://ORACLE_VM_IP:15672

---

## CAPACIDADE ESPERADA

Com uma Oracle VM free tier típica (1 OCPU, 1GB RAM):
- ~1,000 msg/s com 3 consumers
- ~5,000 msg/s com 10 consumers (se mais RAM/CPU)

Com produção remota (sua máquina):
- API pode aceitar 100+ req/s sustained
- Latência: ~50-100ms por requisição

---

## PRÓXIMOS PASSOS OPCIONAIS

1. ADICIONAR AUTENTICAÇÃO
   - API key na header
   - OAuth2 / JWT

2. ADICIONAR BANCO DE DADOS
   - Armazenar histórico de pedidos
   - PostgreSQL no Swarm

3. ADICIONAR SSL/TLS
   - Nginx reverse proxy
   - Let's Encrypt certificates
   - Acesso HTTPS seguro

4. ADICIONAR ALERTAS
   - Prometheus metrics
   - Grafana dashboards
   - Notificações de queue overflow

5. ADICIONAR LOGGING CENTRALIZADO
   - ELK Stack (Elasticsearch, Logstash, Kibana)
   - Todas as mensagens de consumers em um lugar

---

## ARQUIVOS ADICIONADOS/MODIFICADOS

CRIADOS:
✅ producer_api.py           - API REST Flask
✅ load_generator.py         - Stress test tool
✅ CLOUD_DEPLOYMENT.md       - Guia deployment
✅ ORACLE_VM_SETUP.md        - Setup rede

MODIFICADOS:
✅ producer.py               - Env vars support
✅ consumer_payment.py        - Env vars support
✅ consumer_stock.py          - Env vars support
✅ consumer_notification.py   - Env vars support
✅ dashboard.py               - Env vars support
✅ docker-stack.yml           - 6 novos serviços

---

## TESTES RECOMENDADOS

1. Health Check Local:
   docker exec $(docker ps -q -f label=service=tp01_producer_api) \
     curl -s http://localhost:5000/api/health | jq

2. Enviar 1 Pedido:
   curl -X POST http://localhost:5000/api/order \
     -H "Content-Type: application/json" \
     -d '{"customer_id":"CUST-TEST","product_id":"notebook","quantity":1,"amount":2000}'

3. Stress Leve (100 req):
   python3 load_generator.py --target http://localhost:5000/api/order \
                             --total 100 \
                             --concurrency 5

4. Stress Médio (5000 req):
   python3 load_generator.py --target http://localhost:5000/api/order \
                             --total 5000 \
                             --concurrency 20

5. Escalar e repetir:
   docker service scale tp01_consumer_payment=5
   # Teste novamente, observe throughput aumentar

---

## SUPORTE E DEBUGGING

Se algo não funciona:

1. Ver serviços:
   docker service ls

2. Ver logs de um serviço:
   docker service logs tp01_producer_api -f

3. Ver containers:
   docker ps

4. Entrar em um container:
   docker exec -it <container_id> /bin/bash

5. Verificar RabbitMQ cluster:
   docker exec $(docker ps -q -f label=service=tp01_rabbit1) \
     rabbitmqctl cluster_status

6. Remover tudo e recomeçar:
   docker stack rm tp01
   docker swarm leave --force

---

BOM DEPLOY! 🚀
"""
