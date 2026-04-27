"""
CLOUD DEPLOYMENT GUIDE - TP01 com RabbitMQ
===========================================================

Este guia descreve como usar a nova stack com API REST remota.

## ARQUITETURA

RabbitMQ Cluster (3 nós) ← Overlay Network ← Serviços Python:
                                              - producer_api (REST)
                                              - dashboard (SSE)
                                              - 3x consumer_payment
                                              - 3x consumer_stock
                                              - 3x consumer_notification

## PORTS EXPOSTOS (no seu Oracle VM)

- 5672:5672     → AMQP (RabbitMQ protocol, para conexões Python internas)
- 15672:15672   → RabbitMQ Management UI
- 5000:5000     → Producer API (POST /api/order)
- 5001:5000     → Dashboard (GET http://VM_IP:5001)

## STEP 1: Iniciar Swarm e Deploy

No seu Oracle VM:

    docker swarm init

    docker stack deploy -c docker-stack.yml tp01

    # Aguarde ~60 segundos para tudo subir
    docker service ls

    # Unir RabbitMQ em cluster
    bash init_cluster_swarm.sh


## STEP 2: Verificar Status

    # Ver serviços
    docker service ls

    # Ver logs de um serviço
    docker service logs tp01_producer_api -f

    # Acessar RabbitMQ UI
    http://<ORACLE_VM_IP>:15672
    user: admin
    pass: admin123


## STEP 3: Usar a API REST remotamente

### Health Check
    curl http://<ORACLE_VM_IP>:5000/api/health

### Submeter um Pedido
    curl -X POST http://<ORACLE_VM_IP>:5000/api/order \
      -H "Content-Type: application/json" \
      -d '{
        "customer_id": "CUST-0001",
        "product_id": "notebook",
        "quantity": 1,
        "amount": 2999.99
      }'

    Response:
    {
      "status": "ok",
      "order_id": "ORD-A1B2C3D4",
      "event_id": "uuid-...",
      "message": "Pedido enviado à fila com sucesso"
    }

### Dados de Teste
    # Products válidos
    PRODUCTS = ["notebook", "smartphone", "tablet", "monitor", "headset", "keyboard", "mouse"]

    # Exemplo JavaScript (Node.js/Browser)
    fetch('http://<ORACLE_VM_IP>:5000/api/order', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        customer_id: 'CUST-' + Math.random().toString(36).substr(2, 8).toUpperCase(),
        product_id: 'notebook',
        quantity: Math.floor(Math.random() * 5) + 1,
        amount: Math.random() * 5000
      })
    })
    .then(r => r.json())
    .then(console.log)


## STEP 4: Monitorar Dashboard

    http://<ORACLE_VM_IP>:5001

Você verá em tempo real:
- Estado das conectadas ao RabbitMQ
- Número de mensagens por fila
- Número de consumers por serviço
- Animação de mensagens fluindo pelas filas


## STEP 5: Escalar Consumers (para stress test)

### Aumentar replicas de um consumer
    docker service scale tp01_consumer_payment=5
    docker service scale tp01_consumer_stock=3
    docker service scale tp01_consumer_notification=3

### Verificar
    docker service ls

    # Ver os containers
    docker ps

### Ver logs de todos os consumers
    docker service logs tp01_consumer_payment -f


## STRESS TEST - Exemplo Prático

1. Abra o Dashboard
   http://ORACLE_VM_IP:5001

2. Em outro terminal, gere carga:
   python3 load_generator.py --target http://ORACLE_VM_IP:5000/api/order \
                             --concurrency 10 \
                             --total 5000

3. Escale consumers dinamicamente:
   while true; do
     docker service scale tp01_consumer_payment=2
     sleep 60
     docker service scale tp01_consumer_payment=5
   done

4. Observe no dashboard como a vazão (msg/s) muda com o número de consumers


## Exemplo Python para Stress Test

    import requests
    import concurrent.futures
    import time
    import sys

    def submit_order(api_url):
        data = {
            "customer_id": f"CUST-{int(time.time() * 1000) % 10000:04d}",
            "product_id": "notebook",
            "quantity": 1,
            "amount": 2999.99
        }
        try:
            r = requests.post(api_url, json=data, timeout=5)
            return 1 if r.status_code == 201 else 0
        except Exception as e:
            print(f"[ERROR] {e}")
            return 0

    if __name__ == "__main__":
        api_url = "http://ORACLE_VM_IP:5000/api/order"
        total = 5000
        concurrency = 10

        print(f"[STRESS TEST] Enviando {total} pedidos com concorrência {concurrency}...")
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=concurrency) as ex:
            start = time.time()
            futures = [ex.submit(submit_order, api_url) for _ in range(total)]
            results = [f.result() for f in concurrent.futures.as_completed(futures)]
            elapsed = time.time() - start

        successes = sum(results)
        print(f"[RESULTADO] {successes}/{total} sucesso em {elapsed:.2f}s")
        print(f"[THROUGHPUT] {successes/elapsed:.0f} req/s")


## Variáveis de Ambiente (para custom setup)

Se quiser mudar configurações, edite docker-stack.yml:

    environment:
      RABBITMQ_HOST: rabbit1          # Nome do serviço RabbitMQ (ou IP se externo)
      RABBITMQ_USER: admin            # Usuário RabbitMQ
      RABBITMQ_PASS: admin123         # Senha

Os scripts Python (producer_api, dashboard, consumers) usam essas variáveis
para se conectar automaticamente.


## Conectar Producer Externo (fora do Swarm)

Se você quiser rodar producer.py em outro lugar (sua máquina local):

    RABBITMQ_HOST=<ORACLE_VM_IP> \
    RABBITMQ_USER=admin \
    RABBITMQ_PASS=admin123 \
    python producer.py --total 10000


## Troubleshooting

### Services não iniciam
    docker service logs tp01_producer_api

### API retorna "Falha ao conectar ao RabbitMQ"
    - Verifique se RabbitMQ está pronto: docker service ls
    - Verifique se os nós estão clustered: docker exec $(docker ps -q -f label=service=tp01_rabbit1) rabbitmqctl cluster_status

### Dashboard mostra "Conexão Perdida"
    - Verifique RabbitMQ Management API: curl http://localhost:15672/api/overview -u admin:admin123

### Dentro do Docker, Python não consegue conectar
    - Use nome do serviço (rabbit1) não IP
    - Verifique overlay network: docker network ls

## Remover Stack

    docker stack rm tp01

    # Sair do Swarm
    docker swarm leave --force
"""
