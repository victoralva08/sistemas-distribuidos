# Como Usar o Sistema de Pedidos (TP01)

Este guia ensina como rodar todo o ecossistema construído para o projeto, entender a interface visual e guarnece você com o **Roteiro Exato de Apresentação** para mostrar o funcionamento a todos de uma forma super didática!

---

## 1. Subindo a Infraestrutura Docker
Antes de qualquer envio de mensagens, precisamos "ligar os motores" e subir nossa arquitetura.

1. No terminal, na pasta `TP1`, suba o cluster e o banco:
   ```bash
   docker-compose up -d
   ```
2. Inicialize o cluster e ative configurações avançadas (*Quorum Queues*):
   ```bash
   bash init_cluster.sh
   # (Caso use Windows, use Git Bash ou WSL para executar o .sh)
   ```
> **O que isso faz?** Isso cria 3 servidores locais do RabbitMQ que conversam entre si para que os dados nunca caiam, além de um banco de dados PostgreSQL real.

---

## 2. Ligando a Interface Gráfica de Monitoramento
Para não termos que ficar lendo letras difíceis do terminal, criamos um painel web super agradável para avaliar as métricas ao vivo!

1. Instale as bibliotecas Python necessárias (apenas na primeira vez):
   ```bash
   pip install -r requirements.txt
   ```
2. Dedique um terminal rolando o arquivo do site (nunca feche este terminal na apresentação):
   ```bash
   python dashboard.py
   ```
3. **Acesse via navegador URL:** `http://localhost:5000`

---

## 3. Entendendo o Dashboard (Aprenda a Ler os Quadros)
Quando você entra no `http://localhost:5000`, observará quatro blocos no topo e um grande gráfico abaixo. Eis o que significa cada um, de forma bem simples:

### Os Blocos do Topo
* **CONSUMERS ATIVOS:** Indica a quantidade de "trabalhadores" (nossos scripts de consumos) ligados no exato momento, esperando para processar pedidos.
* **CONEXÕES AMQP:** Quantidade de clientes ativamente injetando ou consumindo.
* **MSGS EM FILA (READY):** **Esta é a métrica mais importante!** Mostra quantas mensagens chegaram no sistema, e estão presas (engarrafadas) lá na fila sem ter ninguém para atendê-las no momento. É o estoque de trabalho atrasado.
* **MSGS UNACKED (PROC):** Quantidade de mensagens que saíram da fila e estão "nas mãos" dos sistemas de pagamento neste milissegundo, quase sendo destruídas. Fica alta só quando há uma altíssima lentidão nos pagamentos.

### O Gráfico em Tempo Real
* **Linha Azul Clara (Publish Rate - ENTRANDO):** É a vazão de chegada. Significa quantas compras dos clientes estão explodindo em demanda entrando no sistema (Medido em Mensagens por Segundo).
* **Linha Roxa Escura (Deliver Rate - SAINDO):** É a vazão de resolução! Mostra a velocidade que os seus consumidores de pagamento estão pegando da fila e resolvendo com sucesso (Medido em Mensagens por Segundo).

---

## 4. Roteiro Passo a Passo de Demonstração (O Teatro)
Abra no projetor ou na tela da videoconferência do Microsoft Teams o seu site do Dashboard (http://localhost:5000). A ideia aqui é comandar o sistema manualmente e devagar, aba por aba de terminal.

### Passo 1: Disparando o Gargalo ("Black Friday")
Com a tela do Dashboard zerada, conte à turma que você vai mandar agora mesmo 5.000 requisições maciças pra simular uma loja em pico de uso.
* **Execute em um Novo Terminal:** 
  ```bash
  python producer.py --total 5000
  ```
> **O que este comando faz:** Ele acorda um "robô", cria na mesma hora e atira 5.000 arquivos de compra virtual JSON para dentro do RabbitMQ (da fila `orders.payment`). Em seguida ele para de injetar.<br>
> **O que vai acontecer ali:** No painel você verá a Linha Azul Clara subir forte e a métrica amarela **"MSGS EM FILA (READY)" cravar em 5000**.
> **O que falar na apresentação:** Explique que num sistema normal de servidor comum de PHP ou Python, a máquina teria caído ao tentar gravar 5000 pedidos ao mesmo tempo no banco de dados. Como você usou a teoria de Message Broker da disciplina, as 5000 mensagens estão sãs e salvas, esperando. A aplicação aguentou a porrada!

### Passo 2: Demonstrando o Consumo e a Vazão
Diga à classe que o servidor de pagamentos chegou para trabalhar e vai processar o engarrafamento.
* **Execute em um Novo Terminal:** 
  ```bash
  python consumer_payment.py
  ```
> **O que este comando faz:** Liga o serviço real consumidor de fila. Ele se apresenta à porta da fila `orders.payment` e pede uma mensagem por vez enquanto joga no banco de dados. <br>
> **O que vai acontecer ali:** A mágica! O enorme número amarelo vai começar a **despencar** em queda livre para zero de forma muito rápida. A linha Roxa Escura começará a se desenhar, pois simboliza a vazão *Saindo*.<br>
> **O que falar na apresentação:** Fale sobre Throughput e Vazão; você acabou de provar, visualmente, como o seu ecossistema processa os pagamentos.

### Passo 3: Demonstrando Escalabilidade com Concorrência ("Elasticidade")
Diga à classe que o servidor resolveu, mas queremos ser **duas vezes mais rápidos**.
* **Comando:** Enquanto envia novos dados volumosos (`python producer.py --total 100000`), abra **Duas (ou mais) Abas** ao mesmo tempo e execute em cada uma delas aquele mesmo comando de consumo `python consumer_payment.py`.
> **O que falar na apresentação:** Isso é escalabilidade horizontal da vida real! No dashboard você mostrará a linha Roxa pular para uma capacidade muito maior de atendimento. 

### Passo 4: O Teste Extra (Para tirar nota "10")
Isso atende ao requisito de falhas críticas.
* **Comandos:** Enquanto dados sobem e descem, abra outra aba e desligue na força bruta o contêiner de um nó:
  ```bash
  docker stop rabbit2
  ```
> **O que falar na apresentação:** Use isso como grand-finale. Se 1 banco de dados caísse, era fim de negócio. Como rodamos o cluster com tecnologia de *"Quorum Queues"*, o sistema manteve o serviço em pé perfeitamente entre o nó que sobrou, e no gráfico as quedas das filas continuam sendo limpas perfeitamente! 

---

## 5. Teste Automático de Média Pura (O pc fazendo tudo sozinho)
Caso você queira só extrair o cálculo matemático final e as métricas sem rodar o teatro humano, você pode usar a nossa ferramenta `benchmark.py`.

* **Este comando liga tudo e já te devolve no terminal um relatório final de tempo bruto:**
  ```bash
  python benchmark.py --msgs 100000 --consumers 1
  ```
* **Para rodar gerando o gráfico (.png) para seus arquivos de entrega:**
  ```bash
  python benchmark.py --msgs 100000 --consumers 4
  python benchmark.py --plot-only
  ```
