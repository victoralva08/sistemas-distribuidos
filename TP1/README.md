# TP01 – Sistema de Pedidos com RabbitMQ

## O Cenário

Imagine que você trabalha na equipe de tecnologia de um e-commerce. É véspera de Black Friday e a loja espera receber **milhares de pedidos por segundo**. O problema clássico de sistemas tradicionais é simples: se 5.000 clientes clicam em "Comprar" ao mesmo tempo, o servidor tenta gravar 5.000 pedidos no banco de dados simultaneamente — e trava.

A solução que este projeto demonstra é o uso de um **Message Broker** (no caso, o RabbitMQ). Em vez de processar tudo na hora, o sistema coloca cada pedido em uma **fila** e um conjunto de serviços independentes consome essa fila no seu próprio ritmo. A aplicação não trava, os dados não se perdem, e você pode escalar adicionando mais "trabalhadores" sem mudar uma linha do sistema principal.

---

## A Arquitetura do Sistema

```
                          ┌─────────────────────────────────┐
                          │        RabbitMQ Cluster         │
                          │  (3 nós replicados via Docker)  │
                          │                                 │
[producer.py]  ──────────►│  Exchange: orders.exchange      │
  (gera pedidos)          │                                 │
                          │  Fila: orders.payment  ─────────┼──► [consumer_payment.py]
                          │  Fila: orders.stock    ─────────┼──► [consumer_stock.py]
                          │  Fila: orders.notification ─────┼──► [consumer_notification.py]
                          │  Fila: orders.audit    ─────────┼──► [consumer_audit.py]
                          │                                 │
                          └─────────────────────────────────┘
                                        ▲
                          [dashboard.py] consulta API do RabbitMQ
                          e exibe tudo em http://localhost:5000
```

**Peças do sistema:**

| Arquivo | Papel no sistema |
|---|---|
| `docker-compose.yml` | Sobe o cluster localmente (modo desenvolvimento) |
| `docker-stack.yml` | Sobe o cluster via Docker Swarm (modo orquestrado) |
| `init_cluster.sh` | Une os 3 nós em cluster (para docker-compose) |
| `init_cluster_swarm.sh` | Une os 3 nós em cluster (para Docker Swarm) |
| `producer.py` | O "cliente": gera pedidos aleatórios e os envia ao RabbitMQ |
| `consumer_payment.py` | Serviço que processa pagamentos (valida e aprova) |
| `consumer_stock.py` | Serviço que reserva o produto no estoque |
| `consumer_notification.py` | Serviço que envia a confirmação ao cliente (email/SMS/push) |
| `consumer_audit.py` | Serviço que registra um log de **todos** os eventos do sistema |
| `dashboard.py` | Servidor web do painel de monitoramento em tempo real |
| `benchmark.py` | Ferramenta para medir o throughput com diferentes configurações |

---

## Pré-requisitos

- **Docker Desktop** instalado e rodando
- **Python 3.9+** instalado
- **Git Bash** ou **WSL** (para executar os scripts `.sh` no Windows)

---

## PASSO 1 — Subir a Infraestrutura

Abra um terminal na pasta `TP1` e execute:

```bash
docker-compose up -d
```

**O que este comando faz:**
Ele lê o arquivo `docker-compose.yml` e sobe **3 contêineres** do RabbitMQ (`rabbit1`, `rabbit2`, `rabbit3`), cada um simulando um servidor independente. O `-d` significa "detached" — ou seja, roda em segundo plano sem travar o terminal.

Aguarde cerca de 30 segundos para todos os nós inicializarem completamente.

**Como verificar que funcionou:**
Abra o navegador em `http://localhost:15672` — você verá o painel oficial de gerenciamento do RabbitMQ. Faça login com:
- Usuário: `admin`
- Senha: `admin123`

---

## PASSO 2 — Unir os Nós em Cluster

Ainda no terminal (use Git Bash ou WSL no Windows):

```bash
bash init_cluster.sh
```

**O que este comando faz:**
Por padrão, os 3 contêineres RabbitMQ não se conhecem. Este script entra em cada um deles via `docker exec` e executa os comandos do RabbitMQ para formá-los em um único **cluster**. No final, configura as filas para usar **Quorum Queues** — o tipo de fila que replica os dados entre os nós.

**Por que isso importa:**
Com Quorum Queues, se um dos servidores cair, os outros dois já têm uma cópia dos dados. O sistema não perde nenhum pedido.

---

## PASSO 3 — Instalar as Dependências Python

Execute apenas na primeira vez:

```bash
pip install -r requirements.txt
```

**O que instala:**
- `pika` — biblioteca Python para falar com o RabbitMQ via protocolo AMQP
- `flask` — mini framework web para servir o dashboard
- `requests` — para consultar a API REST do RabbitMQ
- `matplotlib` — para gerar gráficos de benchmark

---

## PASSO 4 — Ligar o Dashboard

Abra um **novo terminal** (mantenha-o aberto durante toda a demonstração) e execute:

```bash
python dashboard.py
```

**O que este comando faz:**
Sobe um servidor web local na porta 5000. Ele consulta a API interna do RabbitMQ a cada segundo e usa **SSE (Server-Sent Events)** para empurrar os dados em tempo real para o navegador — sem precisar dar refresh na página.

Acesse no navegador: **http://localhost:5000**

Você verá quatro métricas no topo e um gráfico em tempo real. Por enquanto estará tudo zerado, pois ainda não enviamos nenhum pedido.

---

## PASSO 5 — O Roteiro de Demonstração

### 🎬 Cena 1: O Gargalo da Black Friday

Abra um **novo terminal** e execute:

```bash
python producer.py --total 5000
```

**O que este comando faz:**
O produtor conecta ao RabbitMQ e, em velocidade máxima, gera e envia **5.000 pedidos** fictícios. Cada pedido é um JSON com: ID do pedido, ID do cliente, produto, quantidade e valor. Ele distribui aleatoriamente entre as 4 routing keys (pagamento, estoque, notificação, auditoria) e encerra quando termina.

**O que você verá no dashboard:**
- A métrica **"Msgs em Fila (Ready)"** vai subir para milhares
- A linha **azul (Publish Rate)** vai disparar e depois cair quando o produtor terminar
- As filas estão cheias de pedidos aguardando — mas nenhum consumer está processando ainda

**O que dizer:**
> *"5.000 pedidos chegaram ao sistema em segundos. Eles estão todos salvos e seguros dentro das filas do RabbitMQ. Nenhum se perdeu, e a aplicação não travou."*

---

### 🎬 Cena 2: O Processamento (Um Worker)

Abra um **novo terminal** e execute:

```bash
python consumer_payment.py
```

**O que este comando faz:**
Liga o serviço de pagamento. Ele se conecta à fila `orders.payment` e começa a retirar mensagens uma por uma. Para cada pedido, simula um tempo de processamento (5–50ms) e, com 2% de chance, rejeita o pagamento — esses pedidos rejeitados vão automaticamente para a **Dead Letter Queue (DLQ)**, uma fila separada de mensagens com falha.

**O que você verá no dashboard:**
- A métrica **"Msgs em Fila"** começa a **cair**
- A linha **roxa (Deliver Rate)** aparece, mostrando a velocidade de consumo
- A métrica **"Consumers Ativos"** mostra 1

**O que dizer:**
> *"O serviço de pagamento começou a trabalhar. Você pode ver o throughput: quantas mensagens por segundo ele consegue processar sozinho."*

---

### 🎬 Cena 3: Escalabilidade Horizontal

Enquanto o producer ainda está enviando (use `--total 100000` para ter tempo), abra **mais 2 terminais** e execute o mesmo comando em cada um:

```bash
# Terminal 2
python consumer_payment.py

# Terminal 3
python consumer_payment.py
```

**O que este comando faz:**
Você está rodando 3 instâncias do mesmo serviço simultaneamente. O RabbitMQ distribui os pedidos entre eles automaticamente — nenhum pedido é processado duas vezes.

**O que você verá no dashboard:**
- **"Consumers Ativos"** sobe para 3
- A linha roxa sobe proporcionalmente — o throughput quase triplica
- A fila esvazia muito mais rápido

**O que dizer:**
> *"Isso é escalabilidade horizontal. Não precisamos de um servidor mais potente — só adicionamos mais workers. E removemos eles igualmente fácil: basta fechar o terminal."*

---

### 🎬 Cena 4: Tolerância a Falhas (O Grand Finale)

Com tudo rodando — producer enviando e consumers processando — abra um **novo terminal** e execute:

```bash
docker stop rabbit2
```

**O que este comando faz:**
Mata na força bruta um dos nós do cluster RabbitMQ, simulando uma falha de servidor em produção.

**O que você verá no dashboard:**
O sistema pode piscar por 1–2 segundos enquanto os clients reconectam, mas o processamento **continua normalmente** com os nós `rabbit1` e `rabbit3`.

**O que dizer:**
> *"Em um banco de dados tradicional, derrubar o servidor seria o fim. Com Quorum Queues, os dados já estavam replicados nos outros dois nós. O sistema sobreviveu sem perder nenhum pedido."*

Para subir o nó novamente:
```bash
docker start rabbit2
```

---

### 🎬 Cena Extra: Os Outros Consumers

Você pode abrir terminais adicionais para ver os outros serviços funcionando em paralelo:

```bash
# Serviço de reserva de estoque
python consumer_stock.py

# Serviço de notificações ao cliente
python consumer_notification.py

# Serviço de auditoria (registra TODOS os eventos)
python consumer_audit.py
```

Cada um deles lê de sua fila específica de forma totalmente independente. O consumer de auditoria é especial: ele usa a routing key `order.#` (onde `#` captura qualquer coisa), então recebe uma cópia de **todas** as mensagens do sistema.

---

## PASSO 6 — Benchmark Automatizado

Se quiser medir o throughput sem fazer a demonstração manual, use:

```bash
# Testa com 1 consumer e 10.000 mensagens
python benchmark.py --msgs 10000 --consumers 1

# Testa com 4 consumers (rode depois do anterior)
python benchmark.py --msgs 10000 --consumers 4

# Gera um gráfico PNG comparando os resultados
python benchmark.py --plot-only
```

**O que acontece:**
O script limpa as filas, roda o producer e sobe N consumers automaticamente, mede quanto tempo levou para processar todas as mensagens e calcula o throughput (msg/s). O `--plot-only` lê os resultados salvos e gera um gráfico `benchmark_plot.png`.

---

## Entendendo o Dashboard

| Indicador | O que significa |
|---|---|
| 🟢 **Status OK** | O RabbitMQ está respondendo normalmente |
| 🟡 **API Offline** | O RabbitMQ não está acessível no momento |
| 🔴 **Conexão Perdida** | O dashboard perdeu conexão com o servidor Flask |
| **Consumers Ativos** | Quantos workers estão conectados e ouvindo as filas |
| **Conexões AMQP** | Total de conexões abertas com o RabbitMQ (producers + consumers) |
| **Msgs em Fila (Ready)** | Pedidos aguardando na fila — o "estoque de trabalho" |
| **Msgs Unacked** | Pedidos que saíram da fila e estão sendo processados agora |
| **Linha Azul** | Publish Rate: velocidade de entrada de mensagens (msg/s) |
| **Linha Roxa** | Deliver Rate: velocidade de processamento pelos consumers (msg/s) |

---

## Encerrando Tudo

Para parar os consumers: `Ctrl+C` em cada terminal.

Para desligar o cluster Docker:
```bash
docker-compose down
```

Para desligar **e apagar os dados** das filas (útil para começar do zero):
```bash
docker-compose down -v
```

---

## Deploy com Docker Swarm (Orquestrador)

O `docker-compose` é ótimo para desenvolvimento local, mas **não é um orquestrador**. O **Docker Swarm** é: ele gerencia os containers automaticamente, reinicia serviços que caem, e foi projetado para rodar em múltiplas máquinas.

O projeto tem um arquivo próprio para isso: `docker-stack.yml`.

### O que muda na prática?

| | docker-compose | Docker Swarm |
|---|---|---|
| Onde roda | Só na sua máquina | Uma ou várias máquinas |
| Rede | Bridge (local) | Overlay (entre máquinas) |
| Restart automático | Não | Sim |
| Comando para subir | `docker-compose up` | `docker stack deploy` |
| Ver serviços | `docker ps` | `docker service ls` |

### Passo a Passo com Swarm

**1. Ativar o modo Swarm na sua máquina:**
```bash
docker swarm init
```
> Isso transforma sua máquina em um **manager node** do Swarm. Em uma infraestrutura real, você adicionaria outras máquinas como **worker nodes** com o token gerado por este comando.

**2. Fazer o deploy do cluster RabbitMQ via Swarm:**
```bash
docker stack deploy -c docker-stack.yml tp01
```
> O Swarm lê o `docker-stack.yml` e cria os 3 serviços RabbitMQ. Aguarde ~30 segundos.

**3. Verificar se os serviços subiram:**
```bash
docker service ls
```
Você deve ver `tp01_rabbit1`, `tp01_rabbit2` e `tp01_rabbit3` com `1/1` réplicas.

**4. Unir os nós em cluster (use Git Bash ou WSL):**
```bash
bash init_cluster_swarm.sh
```
> Este script é a versão do `init_cluster.sh` adaptada para o Swarm. A diferença é que no Swarm os containers não têm nomes fixos — o script os localiza automaticamente pelo nome do serviço.

**5. Acessar o painel web:**
Abra `http://localhost:15672` — deve mostrar os 3 nós no cluster.

**6. O restante do roteiro é igual** — use o mesmo `producer.py`, consumers e `dashboard.py`.

### Demonstrando a Tolerância a Falhas do Swarm

Derrube um serviço:
```bash
docker service scale tp01_rabbit2=0
```

Aguarde e observe o Swarm **reiniciando automaticamente**:
```bash
docker service scale tp01_rabbit2=1
```

> **O que mostrar na apresentação:** diferente do `docker stop` que apenas mata o container, com o Swarm demonstramos que o *orquestrador detecta a falha e age sozinho*, sem intervenção humana. Isso é o que separa orquestração de simples containerização.

### Removendo tudo do Swarm

```bash
# Remove a stack inteira
docker stack rm tp01

# Sai do modo Swarm (volta ao modo normal)
docker swarm leave --force
```
