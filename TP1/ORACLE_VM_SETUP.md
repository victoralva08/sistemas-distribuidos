"""
ORACLE VM NETWORK SETUP
=======================

Para permitir que pessoas acessem sua aplicação remotamente na Oracle VM,
você precisa:

1. Abrir portas no firewall
2. Conferir configurações de rede
3. Expor os serviços (já feito no docker-stack.yml)


## PASSO 1: Configuração Inicial da Oracle VM

# SSH para a VM
ssh ubuntu@<ORACLE_VM_IP>

# Instalar dependências
sudo apt update && sudo apt install -y docker.io git curl

# Adicionar seu usuário ao grupo docker (evita usar sudo)
sudo usermod -aG docker $USER
newgrp docker

# Clonar o repositório
git clone <URL_DO_REPOSITORIO>
cd sistemas-distribuidos/TP1


## OPÇÃO 1: Usando UFW (Firewall Ubuntu/Debian) - RECOMENDADO

    # 1. Criar regra para SSH PRIMEIRO (crítico!)
    sudo ufw allow 22/tcp

    # 2. Habilitar firewall
    sudo ufw enable

    # 3. Liberar portas da aplicação
    sudo ufw allow 5001/tcp     # Producer API (remoto)
    sudo ufw allow 5000/tcp     # Dashboard (remoto)
    sudo ufw allow 15672/tcp    # RabbitMQ Management UI
    
    # 4. Se precisar acesso interno ao RabbitMQ:
    sudo ufw allow from 10.0.0.0/8 to any port 5672/tcp
    
    # 5. Verificar status
    sudo ufw status

    # 6. Remover regra se necessário
    sudo ufw delete allow 5000/tcp


## OPÇÃO 2: Usando iptables (Linux genérico)

    # Liberar portas
    sudo iptables -I INPUT -p tcp --dport 5001 -j ACCEPT
    sudo iptables -I INPUT -p tcp --dport 5000 -j ACCEPT
    sudo iptables -I INPUT -p tcp --dport 15672 -j ACCEPT
    sudo iptables -I INPUT -p tcp --dport 5672 -j ACCEPT

    # Salvar regras (dependente da distribuição)
    # Ubuntu/Debian:
    sudo iptables-save > /etc/iptables/rules.v4

    # CentOS/RHEL:
    sudo service iptables save


## OPÇÃO 3: Oracle Cloud Security Groups (OCI Console) - SE USAR OCI

Se sua Oracle VM está na OCI:

1. Vá para: Networking > Virtual Cloud Networks > [Sua VCN]
2. Clique em: Security Lists > Default Security List
3. Clique "Add Ingress Rules" e adicione:

┌─────────────┬─────────────────┬──────────┬─────────────────────┐
│ Protocol    │ Source CIDR      │ Port     │ Descrição           │
├─────────────┼─────────────────┼──────────┼─────────────────────┤
│ TCP         │ 0.0.0.0/0       │ 5001    │ Producer API        │
│ TCP         │ 0.0.0.0/0       │ 5000    │ Dashboard           │
│ TCP         │ 0.0.0.0/0       │ 15672   │ RabbitMQ UI        │
│ TCP         │ 10.0.0.0/8      │ 5672    │ AMQP interno       │
│ TCP         │ 0.0.0.0/0       │ 22      │ SSH (já existe)     │
└─────────────┴─────────────────┴──────────┴─────────────────────┘

OBS: Use 10.0.0.0/8 para acesso interno ou 0.0.0.0/0 para público


## PASSO 2: Verificar Portas Abertas

    # Ver o que está escutando
    sudo netstat -tuln | grep -E ':(5000|5001|5672|15672)'

    # ou com ss (mais novo)
    sudo ss -tuln | grep -E ':(5000|5001|5672|15672)'

    # Exemplo de resultado esperado:
    # tcp6  0  0 :::5000  :::*  LISTEN
    # tcp6  0  0 :::5001  :::*  LISTEN
    # tcp   0  0 :::15672 :::*  LISTEN


## PASSO 3: Deploy e Verificação

    # Na Oracle VM, execute:
    bash quick_start.sh

    # Aguarde 60 segundos...
    # Ao final, você verá algo como:

    📌 ACESSO DA EQUIPE:
       
       🔵 API de Pedidos (auto-gera dados):
       http://129.154.123.45:5001/api/order
       
       📊 Dashboard em Tempo Real:
       http://129.154.123.45:5000
       
       🐰 RabbitMQ Management UI:
       http://129.154.123.45:15672  (user: admin, pass: admin123)


## PASSO 4: Teste de Conectividade do Seu Computador

    # Obter IP público da Oracle VM
    curl ifconfig.me  (dentro da VM)
    
    # Do seu computador (LOCAL):
    curl http://<ORACLE_VM_IP>:5001/api/health
    
    # Exemplo:
    curl http://129.154.123.45:5001/api/health
    
    # Resposta esperada:
    {
      "status": "healthy",
      "rabbitmq": "connected",
      "routes": ["payment", "stock", "notification"],
      "products": [...]
    }

    # Testar envio de pedidos
    curl -X POST 'http://<ORACLE_VM_IP>:5001/api/order?count=10'


## PASSO 5: Monitorar Remotamente

    # Dashboard em tempo real
    open http://<ORACLE_VM_IP>:5000
    
    # RabbitMQ UI
    open http://<ORACLE_VM_IP>:15672
    
    # Health check
    watch -n 1 'curl -s http://<ORACLE_VM_IP>:5001/api/health'


## Troubleshooting

### "Connection refused" no curl?

    1. Verificar se Docker está rodando:
       ssh ubuntu@<ORACLE_VM_IP>
       docker service ls
    
    2. Verificar firewall:
       sudo ufw status
    
    3. Verificar security group na OCI (se aplicável)
    
    4. Testar conectividade básica:
       telnet <ORACLE_VM_IP> 5001

### "Firewall in Oracle Cloud is blocking"?

    1. Acesse OCI Console
    2. Compute > Instances > [Sua instância]
    3. Primary VNIC > Subnet > Security Lists
    4. Adicione a regra de ingresso conforme OPÇÃO 3 acima

### RabbitMQ UI acessível mas API offline?

    ssh ubuntu@<ORACLE_VM_IP>
    docker service logs tp01_producer_api
    # Procure por erros de conexão

### Lento/timeout nos requests?

    1. Escale os consumers:
       docker service scale tp01_consumer_payment=3
       docker service scale tp01_consumer_stock=3
    
    2. Verifique latência:
       ping <ORACLE_VM_IP>
       curl -w '%{time_total}\n' http://<ORACLE_VM_IP>:5001/api/order


## Configurar DNS (Opcional)

Se você quer um nome amigável tipo "rabbitmq.example.com":

1. Registre o domínio (ex: Route53, Cloudflare, Namecheap)
2. Crie um registro A apontando para <ORACLE_VM_IP>
3. Use: http://rabbitmq.example.com:5001/api/order


## Segurança - Para Produção

⚠️ AVISO: Configuração acima permite acesso público!

Para produção, considere:

    1. Usar HTTPS/SSL (LetsEncrypt + nginx reverse proxy)
    2. Restringir IPs ao invés de 0.0.0.0/0 no firewall
    3. Mudar credenciais RabbitMQ (admin/admin123)
    4. Adicionar autenticação na API (API keys, JWT)
    5. Usar VPN para acesso ao painel RabbitMQ
    6. Monitorar e logar todos os acessos


## SSL/TLS (HTTPS) - Opcional mas Recomendado

Se quiser usar HTTPS (necessário para produção):

1. Obter certificado:
   - Let's Encrypt (gratuito): certbot
   - AWS Certificate Manager / Oracle Cloud

2. Configurar Nginx/HAProxy como proxy reverso:

    # Exemplo com Nginx
    server {
        listen 443 ssl;
        server_name rabbitmq.example.com;
        
        ssl_certificate /etc/letsencrypt/live/rabbitmq.example.com/fullchain.pem;
        ssl_certificate_key /etc/letsencrypt/live/rabbitmq.example.com/privkey.pem;
        
        location /api/ {
            proxy_pass http://localhost:5000;
        }
        
        location / {
            proxy_pass http://localhost:5001;
        }
    }

3. Restart Nginx e acesse https://rabbitmq.example.com


## VPN (se precisar de acesso privado)

Para conexões mais seguras sem expor ao mundo:

1. WireGuard (recomendado, simples)
   - Setup: https://www.wireguard.com/install/

2. OpenVPN (alternativa)

3. SSH Port Forward (solução temporária)
   ssh -L 5000:localhost:5000 user@oracle-vm-ip
   # Agora acesse http://localhost:5000 localmente


## Troubleshooting

### Conexão Recusada (Connection Refused)
  1. Verifique se o serviço está rodando: docker service ls
  2. Verifique os logs: docker service logs tp01_producer_api
  3. Firewall bloqueando? Desabilite temporariamente: sudo ufw disable

### Timeout
  1. Verifique ping: ping <ORACLE_VM_IP>
  2. Verifique rota: traceroute <ORACLE_VM_IP>
  3. Pode ser latência de rede alta

### API responde mas diz "RabbitMQ desconectado"
  1. RabbitMQ está rodando? docker service ls
  2. Logs: docker service logs tp01_rabbit1
  3. Verifique conectividade interna: docker exec <container> ping rabbit1

---

RESUMO RÁPIDO PARA USAR NO ORACLE VM FREE TIER:

  1. SSH into Oracle VM
  
  2. Install Docker (se necessário)
     curl -fsSL https://get.docker.com -o get-docker.sh && sh get-docker.sh
  
  3. Clone ou copie os arquivos TP1 para /home/user/tp01
  
  4. Iniciar Swarm e deploy
     cd /home/user/tp01
     docker swarm init
     docker stack deploy -c docker-stack.yml tp01
     bash init_cluster_swarm.sh
  
  5. Liberar firewall
     sudo ufw allow 5672/tcp
     sudo ufw allow 15672/tcp
     sudo ufw allow 5000/tcp
     sudo ufw allow 5001/tcp
     sudo ufw enable
  
  6. Descobrir IP
     curl ifconfig.me
  
  7. Compartilhar com a equipe
     "Acesse http://<IP>:5000/api/order para enviar pedidos
      Monitore em http://<IP>:5001"
"""
