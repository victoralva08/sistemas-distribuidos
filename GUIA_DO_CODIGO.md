# Como Entender o Código do TP01

Este documento é um **guia de leitura** do projeto. Ele não substitui o README (que ensina a rodar o sistema) — ele ensina a **entender o que o código faz e por quê**.

Leia nesta ordem. Cada seção prepara você para entender a próxima.

---

## Antes de Abrir Qualquer Arquivo

Você precisa ter um modelo mental do sistema. Guarde esta imagem:

```
PRODUTOR  →  [fila 1: pagamentos   ]  →  CONSUMER de pagamento
          →  [fila 2: estoque      ]  →  CONSUMER de estoque
          →  [fila 3: notificações ]  →  CONSUMER de notificação
          →  [fila 4: auditoria    ]  →  CONSUMER de auditoria
```

O **RabbitMQ** fica no meio. Ele é o carteiro: recebe a mensagem do produtor e entrega para a fila certa. Os consumers ficam esperando na fila e processam uma mensagem por vez.

**Pergunta que você deve conseguir responder depois de ler tudo:**
> *"Por que usar filas em vez de chamar os serviços diretamente?"*

Resposta adiantada: porque assim o produtor não precisa esperar o processamento. Ele joga o pedido na fila e segue em frente. Os consumers trabalham no próprio ritmo. Se o consumer cair, a mensagem fica salva na fila esperando — não se perde.

---

## Arquivo 1 — `producer.py`
### O ponto de entrada do sistema

Comece por aqui. O produtor é a peça mais simples de entender porque ele só **faz uma coisa**: gera pedidos e os envia.

### Leia a função `gerar_pedido()` primeiro

```python
def gerar_pedido(numero: int) -> dict:
    return {
        "event_id":   str(uuid.uuid4()),
        "order_id":   f"ORD-{numero:06d}",
        "customer_id": f"CUST-{random.randint(1, 500):04d}",
        "product_id": random.choice(PRODUCTS),
        "quantity":   random.randint(1, 5),
        "amount":     round(random.uniform(19.99, 4999.99), 2),
        "timestamp":  datetime.now(timezone.utc).isoformat(),
    }
```

Isso é um pedido. Um dicionário Python que vai virar JSON e ser enviado para o RabbitMQ. Nada de especial aqui — é só dados fictícios.

### Agora leia `criar_infraestrutura()`

Esta é a função mais importante do arquivo. Ela foi projetada para rodar **uma vez** e configurar toda a estrutura de filas:

**O Exchange:**
```python
channel.exchange_declare(
    exchange=EXCHANGE_NAME,   # "orders.exchange"
    exchange_type="topic",    # tipo que roteia por padrão
    durable=True,
)
```

O Exchange é a **central de distribuição** do RabbitMQ. Toda mensagem chega nele primeiro. O tipo `"topic"` significa que o roteamento é feito por padrões de texto (ex: `order.payment.*` captura `order.payment.new`, `order.payment.retry`, etc.).

**As filas e seus padrões:**
```python
filas = [
    ("orders.payment",      "order.payment.*"),   # só pagamentos
    ("orders.stock",        "order.stock.*"),      # só estoque
    ("orders.notification", "order.notify.*"),     # só notificações
    ("orders.audit",        "order.#"),            # TUDO
]
```

O `#` na fila de auditoria significa *qualquer quantidade de palavras*. Por isso ela recebe uma cópia de todas as mensagens — é o curinga total.

**O Dead Letter Exchange:**
```python
channel.exchange_declare(exchange="orders.dlx", exchange_type="fanout", durable=True)
channel.queue_declare(queue="orders.dlq", durable=True)
```

Quando um consumer rejeita uma mensagem (NACK), ela não some — vai para a **Dead Letter Queue**. É a fila das mensagens que falharam. Útil para debugar e reprocessar pedidos com problema.

### Por fim, leia `executar()` — o loop principal

```python
for i in range(1, total + 1):
    routing_key = random.choice(ROUTING_KEYS)
    pedido = gerar_pedido(i)
    corpo = json.dumps(pedido).encode("utf-8")

    channel.basic_publish(
        exchange=EXCHANGE_NAME,
        routing_key=routing_key,
        body=corpo,
        ...
    )
```

Cada iteração: gera um pedido, escolhe uma routing key aleatória, serializa para JSON e publica no exchange. O RabbitMQ cuida do resto — lê a routing key e decide em qual fila colocar.

**Conceito chave:** o produtor não sabe quem vai processar a mensagem. Ele só sabe para qual exchange e routing key enviar. Isso é **desacoplamento**.

---

## Arquivo 2 — `consumer_payment.py`
### Entendendo o padrão que todos os consumers seguem

Todos os 4 consumers têm a **mesma estrutura**. Se entender este, entende todos.

### A função de callback

```python
def processar_pagamento(ch, method, properties, body):
```

Esta função é registrada no RabbitMQ e chamada automaticamente cada vez que uma mensagem chega. Você não chama ela — o RabbitMQ chama.

Os parâmetros:
- `ch` → o canal. Usado para enviar ACK ou NACK
- `method` → metadados da entrega. Contém o `delivery_tag`, que é o "recibo" da mensagem
- `properties` → cabeçalhos (não usamos aqui)
- `body` → o conteúdo da mensagem em bytes

### O ACK e o NACK — o coração do sistema

```python
# Se aprovado:
ch.basic_ack(delivery_tag=method.delivery_tag)

# Se recusado:
ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)
```

**ACK** (Acknowledgement) = "recebi e processei com sucesso, pode deletar da fila".

**NACK** (Negative Acknowledgement) = "não consegui processar". O `requeue=False` faz a mensagem ir para a Dead Letter Queue em vez de voltar para a fila principal.

**Por que isso importa?** Enquanto o consumer não envia o ACK, o RabbitMQ mantém a mensagem como "em processamento" (Unacked). Se o consumer cair antes de confirmar, o RabbitMQ devolve a mensagem para a fila automaticamente. Nenhum pedido se perde.

### O prefetch_count

```python
channel.basic_qos(prefetch_count=10)
```

Limita quantas mensagens o consumer recebe de uma vez. Sem isso, o RabbitMQ mandaria todas as mensagens disponíveis para o primeiro consumer que se conectar, deixando os outros sem trabalho. Com `prefetch_count=10`, o trabalho é distribuído de forma justa entre todos os consumers ativos.

---

## Arquivo 3 — `consumer_audit.py`
### O que o torna diferente dos outros

O consumer de auditoria é idêntico aos outros em estrutura, mas tem **uma diferença conceitual importante**:

Enquanto os outros consumers escutam filas específicas (`orders.payment`, `orders.stock`...), a fila de auditoria usa a routing key `order.#`, que captura **todos** os eventos do sistema.

Isso significa que para cada pedido publicado pelo produtor, a fila de auditoria recebe uma cópia, independentemente de ser um pagamento, estoque ou notificação. É um padrão chamado de **auditoria transversal** — um serviço que observa tudo sem interferir em nada.

---

## Arquivo 4 — `dashboard.py`
### Como o painel se atualiza sozinho

```python
@app.route("/stream")
def stream():
    def gerador_eventos():
        while True:
            metricas = buscar_metricas()
            yield f"data: {json.dumps(metricas)}\n\n"
            time.sleep(1)

    return Response(gerador_eventos(), content_type="text/event-stream")
```

Este é um **SSE (Server-Sent Events)**. O navegador faz **uma** requisição HTTP para `/stream` e mantém essa conexão aberta. O servidor fica dentro do `while True`, gerando dados a cada 1 segundo com `yield` (que é como o Python "pausar e continuar" uma função).

O `yield` aqui é essencial: em vez de retornar e encerrar a função, ele pausa, empurra os dados para o navegador, e recomeça. Isso cria um stream contínuo de dados sem nunca fechar a conexão.

### De onde vêm os dados?

```python
def buscar_metricas():
    resposta = requests.get(RABBITMQ_API, auth=AUTH, timeout=2)
    dados = resposta.json()
    ...
```

O RabbitMQ tem uma **API REST interna** (Management Plugin) que expõe estatísticas em JSON. O dashboard simplesmente consulta essa API e repassa os dados para o navegador. Por isso o painel funciona sem nada extra — o próprio RabbitMQ já expõe as métricas.

---

## Arquivo 5 — `docker-compose.yml`
### Entendendo a infraestrutura

```yaml
services:
  rabbit1:
    image: rabbitmq:3.13-management
    hostname: rabbit1
    environment:
      RABBITMQ_ERLANG_COOKIE: "TP01_SECRET_COOKIE"
```

**Por que 3 nós?** Alta disponibilidade. Com Quorum Queues, os dados são replicados nos 3 nós. Se um cair, os outros dois continuam com os dados intactos.

**O que é o Erlang Cookie?** O RabbitMQ é construído em Erlang, e o Erlang usa esse "segredo compartilhado" para autenticar comunicação entre nós do cluster. Todos os nós precisam ter o mesmo cookie para formarem um cluster. É como uma senha de entrada no grupo.

**Por que o hostname é fixo?** Quando o `init_cluster.sh` roda um comando como `join_cluster rabbit@rabbit1`, ele usa o hostname `rabbit1` para localizar o nó. Se o hostname fosse aleatório (como o Docker faz por padrão), esse endereçamento não funcionaria.

---

## Arquivo 6 — `docker-stack.yml`
### A diferença para o docker-compose

O `docker-stack.yml` é o equivalente para **Docker Swarm**. A diferença mais importante é a seção `deploy`:

```yaml
deploy:
  replicas: 1
  restart_policy:
    condition: on-failure
    delay: 10s
    max_attempts: 5
```

No docker-compose, se um container cair, ele fica parado até você reiniciar manualmente. Com o Swarm e essa configuração, o orquestrador detecta a queda e reinicia automaticamente. Isso é o que diferencia **containerização** (Docker simples) de **orquestração** (Swarm/Kubernetes).

A rede também muda:

```yaml
networks:
  rabbitmq_net:
    driver: overlay   # bridge no docker-compose → overlay no Swarm
```

A rede `overlay` é uma rede virtual que atravessa múltiplas máquinas físicas. Mesmo que os containers estejam em servidores diferentes, eles se enxergam na mesma rede como se fossem locais.

---

## Conceitos para Saber Explicar na Apresentação

Estes são os conceitos que o professor provavelmente vai perguntar:

### 1. Por que usar RabbitMQ e não chamar os serviços diretamente?

Porque o produtor fica **desacoplado** dos consumers. Ele não sabe se o serviço de pagamento está online, lento ou sobrecarregado — simplesmente coloca o pedido na fila e pronto. O consumer processa quando puder. Isso é **assincronicidade**.

### 2. O que é um Exchange e para que serve?

É o roteador de mensagens do RabbitMQ. O produtor nunca publica direto na fila — ele manda para o Exchange, que decide qual fila recebe a mensagem baseado na `routing_key`. O tipo `topic` permite usar padrões com `*` (uma palavra) e `#` (qualquer quantidade de palavras).

### 3. O que é ACK e por que ele existe?

É a confirmação de que uma mensagem foi processada. Enquanto não chega o ACK, o RabbitMQ considera a mensagem "em andamento". Se o consumer morrer antes de confirmar, o RabbitMQ recoloca a mensagem na fila para outro consumer processar. Garante que **nenhum pedido se perde**.

### 4. O que são Quorum Queues?

São filas que replicam os dados em maioria dos nós (quorum = maioria). Com 3 nós, 2 precisam estar de acordo para confirmar uma operação. Se um nó cair, os outros dois continuam funcionando pois já têm cópia dos dados.

### 5. O que o Swarm adiciona que o docker-compose não tem?

Orquestração. O Swarm monitora os containers e age sozinho: reinicia automaticamente se um cair, distribui serviços entre máquinas, gerencia redes overlay que funcionam entre máquinas físicas diferentes.

---

## Ordem de Leitura — Resumo

```
1. producer.py         → entender como mensagens são criadas e enviadas
2. consumer_payment.py → entender o padrão de consumo (ACK/NACK/callback)
3. consumer_audit.py   → entender o diferencial do routing key "#"
4. dashboard.py        → entender SSE e a API do RabbitMQ
5. docker-compose.yml  → entender a infraestrutura local
6. docker-stack.yml    → entender o que o Swarm adiciona
```
