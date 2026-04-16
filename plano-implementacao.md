# TP01 – RabbitMQ: Sistema de Pedidos de E-commerce
**BCC362 – Sistemas Distribuídos | Plano de Implementação v3.0**

---

## Novidades da Implementação (Dashboard & Benchmark)
Foi finalizada a implementação técnica contemplando:
1. **O Dashboard em Flask+SSE** (`dashboard.py`, `templates/index.html`): Interface rica, operando via HTTP puxando métricas da API de gerenciamento (`/api/overview`) em tempo-real. Exibe o consumo (Deliver/Publish Rate) com uso da biblioteca Chart.js.
2. **Automação do Benchmark** (`benchmark.py`): Um script orquestrador que injeta as mensagens na fila via subprocessos, dispara e conta o tempo dos consumidores até esvaziarem a carga e compila graficamente via `matplotlib`.

---

## Arquitetura do Sistema

Cluster RabbitMQ de 3 nós com as seguintes configurações ativas:

- **Topic Exchange** principal (`orders.exchange`) com 4 filas especializadas
- **Quorum Queues** em todos os nós (replicação via Raft)
- **Dead Letter Queue** (`orders.dlq`) para mensagens rejeitadas ou expiradas
- **ACK manual** em todos os consumers
- **PostgreSQL** como banco de persistência dos pedidos processados
- **Dashboard web** em tempo real (Flask + SSE) com métricas do cluster

### Filas e roteamento

| Fila | Routing Key | Consumer |
|---|---|---|
| `orders.payment` | `order.payment.*` | consumer_payment.py |
| `orders.stock` | `order.stock.*` | consumer_stock.py |
| `orders.notification` | `order.notify.*` | consumer_notification.py |
| `orders.audit` | `order.#` | consumer_audit.py (todas as mensagens) |
| `orders.dlq` | — | Dead Letter (sem consumer ativo) |

---

## Instalação — 4 camadas

### 1. Single node (local)
```bash
docker run -d --hostname rabbit1 --name rabbitmq \
  -p 5672:5672 -p 15672:15672 \
  rabbitmq:3.13-management
```

### 2. Cluster local com Docker Compose
```yaml
# docker-compose.yml
services:
  rabbit1:
    image: rabbitmq:3.13-management
    hostname: rabbit1
    environment:
      RABBITMQ_ERLANG_COOKIE: "SECRET_COOKIE"
    ports:
      - "15672:15672"

  rabbit2:
    image: rabbitmq:3.13-management
    hostname: rabbit2
    environment:
      RABBITMQ_ERLANG_COOKIE: "SECRET_COOKIE"
    depends_on: [rabbit1]

  rabbit3:
    image: rabbitmq:3.13-management
    hostname: rabbit3
    environment:
      RABBITMQ_ERLANG_COOKIE: "SECRET_COOKIE"
    depends_on: [rabbit1]
```

Após subir, unir os nós ao cluster:
```bash
docker exec rabbit2 rabbitmqctl stop_app
docker exec rabbit2 rabbitmqctl join_cluster rabbit@rabbit1
docker exec rabbit2 rabbitmqctl start_app

docker exec rabbit3 rabbitmqctl stop_app
docker exec rabbit3 rabbitmqctl join_cluster rabbit@rabbit1
docker exec rabbit3 rabbitmqctl start_app
```

Ativar Quorum Queues como padrão:
```bash
docker exec rabbit1 rabbitmqctl set_policy quorum-default ".*" \
  '{"queue-mode":"lazy"}' --apply-to queues
```

### 3. Cluster em cloud pública — GCP Free Tier

**Passo a passo:**

1. Criar 3 VMs `e2-micro` no GCP (gratuitas no Free Tier) com Ubuntu 22.04
2. Em cada VM, instalar Docker:
```bash
curl -fsSL https://get.docker.com | sh
```
3. Na VM `rabbit1`, iniciar o Swarm:
```bash
docker swarm init
docker swarm join-token worker  # copiar o comando gerado
```
4. Nas VMs `rabbit2` e `rabbit3`, executar o join:
```bash
docker swarm join --token <TOKEN> <IP_RABBIT1>:2377
```
5. Deploy do stack:
```bash
docker stack deploy -c docker-compose.yml rabbitmq_cluster
```

### 4. Kubernetes (produção real)

Para produção, a escolha seria o **RabbitMQ Cluster Operator**:

```bash
# Instalar o operator
kubectl apply -f https://github.com/rabbitmq/cluster-operator/releases/latest/download/cluster-operator.yml

# Criar o cluster
kubectl apply -f - <<EOF
apiVersion: rabbitmq.com/v1beta1
kind: RabbitmqCluster
metadata:
  name: rabbitmq-cluster
spec:
  replicas: 3
EOF
```

Para este trabalho, optamos pelo **Docker Swarm** por ser suficiente para demonstração e mais simples de configurar ao vivo. O Kubernetes seria a escolha em um ambiente de produção real.

---

## A Aplicação — Sistema de Pedidos de E-commerce

### Por que e-commerce é um problema distribuído difícil

Sistemas de e-commerce enfrentam desafios clássicos de computação distribuída:

- **Idempotência em pagamentos** — o mesmo pedido não pode ser cobrado duas vezes, mesmo se a mensagem for reentregue
- **Consistência eventual** — estoque, pagamento e notificação são atualizados de forma assíncrona
- **Saga Pattern** — cada etapa do pedido é uma transação independente com rollback próprio em caso de falha
- **Pico de carga** — eventos como Black Friday exigem escalonamento sem downtime

O RabbitMQ resolve esses desafios com: ACK manual (garante at-least-once delivery), DLQ (isola falhas), e escalonamento horizontal de consumers sem interrupção.

### Fluxo de uma mensagem no sistema

```
Producer (pedido novo)
    │
    ▼
orders.exchange  (Topic Exchange)
    │
    ├──► orders.payment     ──► consumer_payment  ──► PostgreSQL (payments)
    ├──► orders.stock       ──► consumer_stock    ──► PostgreSQL (inventory)
    ├──► orders.notification──► consumer_notify   ──► email/SMS
    └──► orders.audit       ──► consumer_audit    ──► PostgreSQL (audit_log)
                                                             │
                                          falha / TTL ──► orders.dlq
```

---

## Benchmark de Throughput

Execute o script de benchmark e registre os valores reais:

```bash
python benchmark.py --msgs 100000 --consumers 1
python benchmark.py --msgs 100000 --consumers 2
python benchmark.py --msgs 100000 --consumers 4
```

Apresentar gráfico gerado com matplotlib mostrando mensagens/segundo por número de consumers. **Não usar valores estimados — apenas os medidos.**

---

## Demo ao Vivo — Roteiro Técnico

### Tolerância a falhas
```bash
# Com o sistema rodando e enviando mensagens, derrubar rabbit2:
docker stop rabbit2

# Mostrar no Management UI que o cluster continua com 2 nós
# Mostrar que mensagens continuam sendo processadas
# Recriar o nó:
docker start rabbit2
```

### Escalonamento de consumers
```bash
# Subir um segundo consumer_payment sem parar o sistema:
docker-compose up -d --scale consumer_payment=3
# Mostrar no dashboard que o throughput aumenta
```

---

## Roteiro de Apresentação (30 minutos)

| Tempo | Seção | Conteúdo | Item |
|---|---|---|---|
| 0–5 min | O que é RabbitMQ | AMQP, casos de uso, deployments famosos (Instagram, Reddit), quando usar vs Kafka | 1 |
| 5–10 min | Arquitetura interna | Exchanges, Queues, Bindings, VHosts, Plugins, Management UI ao vivo | 2 |
| 10–15 min | Instalação | Single node → Docker → Cluster → Docker Swarm → GCP → Quorum Queues → Kubernetes | 3 |
| 15–20 min | A aplicação | Desafios do e-commerce distribuído, sistema rodando, dashboard ao vivo, tolerância a falhas, escalonamento, throughput medido | 4 |
| 20–30 min | Questionários | Perguntas do professor + Q&A preparado | 5 |

---

## Questionários — 8 Perguntas com Respostas

**Q1. Qual a diferença entre RabbitMQ e Apache Kafka?**

RabbitMQ é um message broker orientado a filas (push-based), ideal para tarefas transacionais com roteamento complexo e ACK por mensagem. Kafka é um log de eventos distribuído (pull-based), otimizado para alta taxa de ingestão e replay de eventos. RabbitMQ entrega e apaga a mensagem; Kafka retém e permite reprocessamento.

---

**Q2. O que é um Exchange e quais os tipos disponíveis?**

Exchange é o componente que recebe mensagens do producer e as roteia para filas. Tipos: **Direct** (routing key exata), **Topic** (wildcards `*` e `#`), **Fanout** (broadcast para todas as filas) e **Headers** (roteamento por atributos de cabeçalho).

---

**Q3. O que são Quorum Queues e por que foram escolhidas?**

Quorum Queues são filas replicadas baseadas no algoritmo de consenso Raft. Uma mensagem só é confirmada após ser gravada na maioria dos nós. Substituem as Classic Mirrored Queues por serem mais seguras e previsíveis em caso de falha de nó.

---

**Q4. O que acontece se um nó cai sem haver quorum?**

Se o número de nós disponíveis cai abaixo do quorum (maioria), a fila fica indisponível até que nós suficientes voltem ou sejam adicionados. Isso é intencional: prioriza consistência sobre disponibilidade (CP no teorema CAP).

---

**Q5. O que é Dead Letter Queue e quando uma mensagem vai para ela?**

DLQ é uma fila especial que recebe mensagens que não puderam ser processadas. Uma mensagem vai para a DLQ quando: (1) é rejeitada com `basic.nack` sem requeue, (2) expira o TTL da mensagem ou da fila, ou (3) a fila atinge o limite máximo de mensagens.

---

**Q6. Como funciona o ACK manual e por que é importante?**

No ACK manual, o consumer só confirma (`basic.ack`) após processar com sucesso. Se o consumer morrer antes, o RabbitMQ reentrega a mensagem. Isso garante _at-least-once delivery_. Sem ACK manual (auto-ack), a mensagem é removida ao ser entregue, mesmo que o processamento falhe.

---

**Q7. Como escalar consumers sem parar o sistema?**

Basta iniciar novas instâncias do consumer apontando para a mesma fila. O RabbitMQ distribui as mensagens em round-robin automaticamente (competing consumers pattern). Com `prefetch_count` configurado, cada consumer recebe apenas N mensagens de uma vez. Não há downtime.

---

**Q8. Por que Docker Swarm e não Kubernetes neste trabalho?**

Para o escopo de demonstração, Docker Swarm é suficiente e muito mais simples de configurar. Kubernetes oferece mais recursos (auto-scaling, rolling updates, health checks avançados) e seria a escolha em produção real usando o RabbitMQ Cluster Operator. Conhecemos ambos e escolhemos o mais adequado ao contexto.

---

## Checklist de Entrega

- [x] Cluster 3 nós RabbitMQ via Docker Compose (local)
- [x] Mesmo cluster via Docker Swarm em 3 VMs no GCP Free Tier
- [x] Slide comparando Docker Swarm vs Kubernetes
- [x] Topic Exchange com 4 filas especializadas
- [x] Quorum Queues ativadas e demonstradas
- [x] Dead Letter Queue configurada e demonstrada
- [x] Producer enviando 100k mensagens
- [x] 4 consumers especializados salvando no PostgreSQL
- [x] Dashboard web com métricas em tempo real (Flask + SSE)
- [x] Demo de tolerância a falhas ao vivo
- [x] 2 slides sobre desafios distribuídos do e-commerce
- [x] Diagrama de sequência real do fluxo no sistema
- [x] Throughput medido com valores reais + gráfico
- [x] 8 questionários estudados por todos do grupo
- [x] README completo com instruções de execução
