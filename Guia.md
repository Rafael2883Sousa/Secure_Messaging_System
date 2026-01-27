# Guia Rápido de Utilização

## Instalação

```bash
#Clonar Repositório
git clone https://github.com/Rafael2883Sousa/Secure_Messaging_System.git

# Navegar para o diretório
cd Secure_messaging_system

# Instalar dependências
pip3 install cryptography

```

## Teste Rápido

### 1. Testar Primitivas Criptográficas

```bash
python3 teste_systema.py
```

Este script testa:
- Geração de chaves ECC
- Assinaturas ECDSA
- ECDH
- HKDF
- AES-GCM
- Fluxo completo Alice ↔ Bob

### 2. Testar Servidor Automaticamente

```bash
python3 teste_servidor.py
```

Este script:
- Inicia servidor automaticamente
- Testa registo de utilizadores
- Testa consultas de chaves
- Testa listagem de utilizadores
- Encerra servidor

## Demonstração Completa

### Terminal 1: Servidor

```bash
git clone https://github.com/Rafael2883Sousa/Secure_Messaging_System.git
cd Secure_messaging_system
python3 servidor/servidor.py
```

Saída esperada:
```
[*] Servidor de Registo iniciado em 127.0.0.1:5000
[*] Base de dados: registration_authority.db
[*] A aguardar conexões...
```

### Terminal 2: Cliente Alice

```bash
cd Secure_messaging_system
python3 cliente/client.py alice --listen-port 6000
```

Saída esperada:
```
[*] A gerar par de chaves ECC (SECP256R1)...
[+] Par de chaves gerado com sucesso
[*] A registar utilizador 'alice' no servidor...
[+] Registo efetuado com sucesso!
[*] A escutar em 0.0.0.0:6000
[*] Cliente 'alice' pronto!
[*] Porta de escuta: 6000
```

Menu:
```
=== Menu ===
1. Listar utilizadores
2. Estabelecer sessão com peer
3. Enviar mensagem
4. Sair
============
```

### Terminal 3: Cliente Bob

```bash
cd Secure_messaging_system
python3 cliente/client.py bob --listen-port 6001
```

### Passo a Passo: Alice envia mensagem para Bob

**No terminal de Alice:**

1. Listar utilizadores (opcional):
   ```
   Escolha uma opção: 1
   ```
   
   Saída:
   ```
   === Utilizadores Registados ===
     - alice (registado em 2025-01-08T...)
     - bob (registado em 2025-01-08T...)
   ================================
   ```

2. Estabelecer sessão com Bob:
   ```
   Escolha uma opção: 2
   ID do peer: bob
   Endereço do peer: 127.0.0.1
   Porta do peer: 6001
   ```
   
   Saída:
   ```
   [*] A estabelecer sessão segura com 'bob'...
   [*] A solicitar chave pública de 'bob'...
   [+] Chave pública de 'bob' obtida
   [+] Sessão segura estabelecida com 'bob'
   [+] Chave de sessão derivada via HKDF + SHA-256
   ```

3. Enviar mensagem:
   ```
   Escolha uma opção: 3
   ID do destinatário: bob
   Mensagem: Olá Bob! Esta mensagem é confidencial e autenticada!
   ```
   
   Saída:
   ```
   [+] Mensagem enviada para 'bob' (cifrada e assinada)
   ```

**No terminal de Bob (receção automática):**

```
[+] Pedido de sessão de 'alice'
[+] Sessão estabelecida com 'alice'

[alice]: Olá Bob! Esta mensagem é confidencial e autenticada!
```

### Bob responde para Alice

**No terminal de Bob:**

1. Como a sessão já foi estabelecida por Alice, Bob pode responder diretamente:
   ```
   Escolha uma opção: 3
   ID do destinatário: alice
   Mensagem: Olá Alice! Recebi a tua mensagem segura!
   ```

**No terminal de Alice (receção automática):**

```
[bob]: Olá Alice! Recebi a tua mensagem segura!
```

## Verificação de Segurança

Durante a execução, pode-se verificar:

1. **Confidencialidade**: 
   - Wireshark ou outro para capturar tráfego
   - Verá apenas dados cifrados (base64)

2. **Integridade**:
   - Modifique manualmente um ciphertext
   - A verificação GCM tag falhará

3. **Autenticidade**:
   - Assinatura ECDSA garante origem
   - Cada mensagem exibe "[remetente]: mensagem"

## Estrutura de Arquivos Criados

```
/Secure_messaging_system/
├── comon/
│   ├── __init__.py
│   ├── primitivas_crypto.py    # ✓ Primitivas criptográficas
│   └── protocol.py             # ✓ Protocolo de comunicação
├── servidor/
│   ├── __init__.py
│   ├── db.py                    # ✓ Gestão SQLite
│   └── servidor.py              # ✓ Servidor (AR)
├── cliente/
│   ├── __init__.py
│   └── client.py                # ✓ Cliente CLI
├── teste_sistema.py             # ✓ Teste de primitivas
├── teste_servidor.py            # ✓ Teste do servidor
├── demo.sh                      # ✓ Script de demonstração
├── README.md                    # ✓ Documentação principal
├── RELATORIO_TECNICO.md         # ✓ Relatório técnico detalhado
└── GUIA.md                      # ✓ Este arquivo
```

## Base de Dados

Após execução, será criado:
- `autoridade_registro.db`: Base SQLite com utilizadores registados

Estrutura da tabela:
```sql
CREATE TABLE users (
    user_id TEXT PRIMARY KEY,
    public_key TEXT NOT NULL,
    registration_date TEXT NOT NULL
);
```

## Solução de Problemas

### Servidor não inicia

```bash
# Verifica se porta está em uso
lsof -i :5000

# Usa porta diferente
python3 servidor/servidor.py --port 5001
```

### Cliente não conecta

```bash
# Verifica se servidor está a correr
telnet 127.0.0.1 5000

# Verifica firewall
sudo iptables -L
```

### Erro de biblioteca

```bash
# Reinstala cryptography
pip3 install --upgrade cryptography
```

## Comandos Úteis

### Limpar base de dados

```bash
rm autoridade_registro.db
```

### Ver conteúdo da base de dados

```bash
sqlite3 autoridade_registro.db "SELECT * FROM users;"
```

### Executar demonstração completa

```bash
./demo.sh
```

## Primitivas Implementadas

| Primitiva | Propósito | Algoritmo |
|-----------|-----------|-----------|
| ECC | Chaves assimétricas | SECP256R1 |
| ECDH | Troca de chaves | Diffie-Hellman sobre ECC |
| ECDSA | Assinaturas digitais | ECDSA + SHA-256 |
| HKDF | Derivação de chaves | HKDF + SHA-256 |
| AES-GCM | Cifra simétrica | AES-256-GCM (AEAD) |
| SHA-256 | Hash | SHA-256 |

## Propriedades de Segurança Garantidas

✅ **Confidencialidade**: AES-256-GCM  
✅ **Integridade**: GCM tag + verificação  
✅ **Autenticidade**: Assinaturas ECDSA  
✅ **Forward Secrecy**: Chaves efémeras ECDH  
✅ **Não-Repúdio**: Assinaturas digitais  

## Suporte

Para mais detalhes técnicos, consulte:
- `README.md`: Documentação completa
- `RELATORIO_TECNICO.md`: Análise técnica detalhada