# TP01 – Sistemas Distribuídos: RabbitMQ

## Visão Geral

O grupo implementará um **sistema de processamento distribuído de pedidos de e-commerce** usando RabbitMQ como middleware de mensageria. A aplicação simula um fluxo real de pedidos online sendo processados em paralelo por múltiplos consumidores especializados, demonstrando as capacidades de escalabilidade, tolerância a falhas e roteamento inteligente do RabbitMQ.

A ideia central é impressionar o professor com uma aplicação **real, visualmente rica e tecnicamente completa**, que vai além do simples "enviar e receber mensagem".

---

## 🎯 Aplicação Escolhida: Sistema de Pedidos de E-commerce

### Por que essa aplicação?
- É familiar e fácil de entender para qualquer pessoa
- Demonstra **múltiplos tipos de exchanges** (direct, fanout, topic)
- Justifica naturalmente o uso de **filas separadas por tipo de tarefa**
- Permite demonstrar **escalabilidade** e **tolerância a falhas** de forma clara
- Tem um **dashboard visual** para impressionar na apresentação

### Fluxo da aplicação:
```
[Producer] → pedidos chegam com tipo: payment | shipping | notification | fraud_check
     ↓
[Exchange: orders (topic)]
     ↓               ↓              ↓               ↓
[Queue: payment] [Queue: shipping] [Queue: notify] [Queue: fraud]
     ↓               ↓              ↓               ↓
[Consumer 1]    [Consumer 2]   [Consumer 3]    [Consumer 4]
     ↓
[PostgreSQL] ← salva todos os eventos processados
     ↓
[Dashboard Web] ← exibe métricas em tempo real
```

---

## 📁 Estrutura de Arquivos Final

```
TP1/
├── docker-compose.yml         ← cluster RabbitMQ (3 nós) + PostgreSQL + Dashboard
├── requirements.txt
├── producer.py                ← envia pedidos simulados em massa
├── consumer_payment.py        ← processa pagamentos
├── consumer_shipping.py       ← processa envios
├── consumer_notification.py   ← processa notificações
├── consumer_fraud.py          ← detecta fraudes
├── dashboard/
│   └── app.py                 ← dashboard web (Flask) com métricas em tempo real
└── README.md
```

---

## 🔧 O que será implementado (por etapas)

### Etapa 1 – Infraestrutura: Cluster RabbitMQ com 3 nós + Docker
**Arquivo: `docker-compose.yml`** (reescrita completa)

- **3 nós RabbitMQ** em cluster (rabbit1, rabbit2, rabbit3)
- **Quorum Queues** ativadas (tolerância a falhas real)
- **PostgreSQL** para persistência dos eventos
- **Management UI** exposta na porta 15672
- Variáveis de ambiente configuradas

> [!IMPORTANT]
> Este é o item que mais impressiona o professor: um cluster real de 3 nós com tolerância a falhas demonstrável.

---

### Etapa 2 – Producer aprimorado
**Arquivo: `producer.py`** (melhoria sobre o existente)

O producer atual já envia 1000 mensagens com `uuid`, `task`, `priority` e `timestamp`. Vamos melhorar para:
- Usar **Topic Exchange** em vez de fila direta
- Adicionar campo `amount` (valor do pedido) e `customer_id`
- Enviar para routing keys específicas: `order.payment`, `order.shipping`, `order.notification`, `order.fraud`
- Mostrar **taxa de envio em tempo real** (mensagens/segundo)
- Suporte a `--total` via argumento de linha de comando para escalar o volume

---

### Etapa 3 – Consumers especializados (4 consumers)
**Arquivos: `consumer_payment.py`, `consumer_shipping.py`, `consumer_notification.py`, `consumer_fraud.py`**

Cada consumer vai:
- Processar sua fila específica com lógica simulada (sleep aleatório)
- Fazer **ACK manual** (já implementado no consumer atual)
- Salvar resultado no **PostgreSQL**
- Implementar **Dead Letter Queue** (mensagens que falham vão para fila de erro)
- Exibir log colorido no terminal

---

### Etapa 4 – Dashboard Web em tempo real
**Arquivo: `dashboard/app.py`** (Flask + Server-Sent Events)

Dashboard visual que exibe:
- 📊 Total de mensagens processadas por tipo
- ⚡ Throughput em tempo real (msg/s)
- 🔴 Mensagens na fila (pendentes)
- 💀 Dead Letter Queue (falhas)
- 🖥️ Status dos 3 nós do cluster

---

### Etapa 5 – Demonstração de Tolerância a Falhas
Script de demonstração:
```bash
# Derrubar um nó do cluster
docker stop rabbit2

# O sistema continua funcionando!
# Depois de alguns segundos, subir de volta
docker start rabbit2
# O nó re-sincroniza automaticamente
```

---

## 🏗️ Arquitetura RabbitMQ que será apresentada

```
┌─────────────────────────────────────────┐
│           RabbitMQ Cluster              │
│                                         │
│  ┌─────────┐  ┌─────────┐  ┌─────────┐ │
│  │ rabbit1 │←→│ rabbit2 │←→│ rabbit3 │ │
│  │(primary)│  │         │  │         │ │
│  └─────────┘  └─────────┘  └─────────┘ │
│                                         │
│  Exchange: orders (topic)               │
│  ┌──────────┬───────────┬────────────┐  │
│  │ payment  │ shipping  │ notify     │  │
│  │ (quorum) │ (quorum)  │ (quorum)   │  │
│  └──────────┴───────────┴────────────┘  │
└─────────────────────────────────────────┘
```

---

## 📊 Demonstração de Escalabilidade

Mostrar o sistema rodando com volumes crescentes:

| Volume | Consumers | Throughput esperado |
|--------|-----------|---------------------|
| 1.000 mensagens | 1 por tipo | ~500 msg/s |
| 10.000 mensagens | 2 por tipo | ~1.000 msg/s |
| 100.000 mensagens | 4 por tipo | ~2.000 msg/s |

---

## 📑 Roteiro da Apresentação (20 min)

| Tempo | Seção | Conteúdo |
|---|---|---|
| 0-5 min | **O que é RabbitMQ** | História, AMQP, onde é usado (Instagram, Reddit, WeWork), maiores deployments |
| 5-10 min | **Arquitetura Interna** | Exchanges, Queues, Bindings, Producers, Consumers, VHosts, Plugins |
| 10-15 min | **Instalação** | Single node → Docker → Cluster 3 nós → Quorum Queues → Tolerância a falhas |
| 15-20 min | **Demo ao vivo** | Rodar o sistema, mostrar dashboard, derrubar um nó, escalar consumers |

---

## ✅ Checklist do que será entregue

- `[ ]` Cluster de 3 nós RabbitMQ via Docker Compose
- `[ ]` Topic Exchange com 4 filas especializadas
- `[ ]` Quorum Queues ativadas (tolerância a falhas)
- `[ ]` Dead Letter Queue configurada
- `[ ]` Producer enviando 100k mensagens com métricas
- `[ ]` 4 consumers especializados salvando no PostgreSQL
- `[ ]` Dashboard web com métricas em tempo real
- `[ ]` Demonstração de tolerância a falhas (nó caindo e voltando)
- `[ ]` README completo com instruções de execução

---

## 🚀 Diferenciais que vão impressionar o professor

1. **Cluster real de 3 nós** (não só um container isolado)
2. **Quorum Queues** — recurso avançado de tolerância a falhas
3. **Dead Letter Queue** — tratamento de falhas profissional
4. **Dashboard em tempo real** — visual e impactante na apresentação
5. **Escalabilidade demonstrada** — aumentar consumers sem parar o sistema
6. **100.000 mensagens** processadas ao vivo

> [!NOTE]
> A base do código (producer.py, consumer.py, docker-compose.yml) já existe e será evoluída — não começamos do zero!
