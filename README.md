# Sistema de Mensagens Seguras com Registo de Utilizadores

Sistema de mensagens seguras desenvolvido para a disciplina de Criptografia Moderna.

## Descrição

Sistema cliente-servidor que implementa:
- **Autoridade de Registo (AR)**: Servidor central que mantém registo de utilizadores e suas chaves públicas
- **Cliente CLI**: Aplicação de linha de comando para troca de mensagens seguras

## Primitivas Criptográficas

- **ECC**: Curva SECP256R1
- **ECDH**: Troca de chaves Diffie-Hellman sobre curvas elípticas
- **ECDSA + SHA-256**: Assinaturas digitais
- **HKDF + SHA-256**: Derivação de chaves
- **AES-256-GCM**: Cifra simétrica autenticada (AEAD)
- **SHA-256**: Função hash

## Arquitetura

### Servidor (Autoridade de Registo)
- Mantém base de dados SQLite com:
  - ID do cliente
  - Chave pública
  - Data/hora de registo
- Permite:
  - Registo de novos clientes
  - Consulta de chaves públicas
  - Listagem de utilizadores registados
- Verifica assinaturas digitais nos pedidos de registo
- **Nunca armazena**: chaves privadas, chaves simétricas, mensagens

### Cliente
- Gera par de chaves ECC localmente
- Regista-se no servidor com assinatura digital
- Solicita chaves públicas de outros clientes
- Estabelece sessões seguras ponto-a-ponto usando ECDH
- Deriva chaves de sessão via HKDF
- Troca mensagens cifradas com AES-GCM
- Assina digitalmente todas as mensagens

## Instalação

### Requisitos
- Python 3.11+
- Biblioteca `cryptography`

### Instalar dependências
```bash
pip install cryptography
```

## Utilização

### 1. Iniciar o Servidor

Em um terminal:

```bash
cd /app/secure_messaging_system
python3 servidor/servidor.py
```

Opções disponíveis:
```bash
python3 servidor/servidor.py --host 127.0.0.1 --port 5000 --db autoridade_registro.db
```

O servidor ficará à escuta na porta 5000 (padrão).

### 2. Iniciar Clientes

Em terminais separados, inicie dois ou mais clientes:

**Cliente Alice:**
```bash
python3 cliente/client.py alice --listen-port 6000
```

**Cliente Bob:**
```bash
python3 client/client.py bob --listen-port 6001
```

Cada cliente:
1. Gera automaticamente um par de chaves ECC
2. Regista-se no servidor
3. Fica à escuta para conexões de entrada

### 3. Estabelecer Sessão Segura

No cliente Alice, escolha a opção 2 do menu:
```
Escolha uma opção: 2
ID do peer: bob
Endereço do peer: 127.0.0.1
Porta do peer: 6001
```

Isto estabelece uma sessão segura usando ECDH.

### 4. Enviar Mensagens

No cliente Alice, escolha a opção 3:
```
Escolha uma opção: 3
ID do destinatário: bob
Mensagem: Olá Bob, esta mensagem é segura!
```

A mensagem será:
1. Cifrada com AES-256-GCM
2. Assinada com ECDSA
3. Enviada através da sessão segura

Bob receberá a mensagem automaticamente, que será:
1. Verificada (assinatura)
2. Verificada (integridade)
3. Decifrada

### 5. Listar Utilizadores

Opção 1 do menu lista todos os utilizadores registados no servidor.

## Fluxo de Estabelecimento de Sessão

1. **Cliente A** solicita ao servidor a chave pública de **B**
2. **A** conecta-se a **B** e gera chave ECDH efémera
3. **A** envia sua chave pública efémera para **B**
4. **B** gera sua própria chave efémera e responde
5. **A** e **B** calculam o segredo partilhado (ECDH)
6. **A** e **B** derivam a mesma chave AES-256 via HKDF
7. Comunicação passa a ser simétrica usando AES-GCM

**Importante**: A chave simétrica nunca é transmitida pela rede.

## Formato das Mensagens

### Mensagem Segura (JSON)
```json
{
  "type": "SECURE_MESSAGE",
  "data": {
    "from": "alice",
    "encrypted_data": {
      "nonce": "base64...",
      "ciphertext": "base64...",
      "tag": "base64...",
      "signature": "base64..."
    }
  }
}
```

## Estrutura do Projeto

```
secure_messaging_system/
├── comon/
│   ├── primitivas_crypto.py  # Primitivas criptográficas
│   └── protocol.py            # Protocolo de comunicação
├── servidor/
│   ├── db.py            # Gestão da base de dados SQLite
│   └── servidor.py              # Servidor de Registo (AR)
├── cliente/
│   └── client.py              # Cliente de mensagens seguras
└── README.md
```

## Funcionalidades Avançadas Implementadas

✅ Assinatura digital de todas as mensagens (ECDSA)  
✅ Autenticação cliente → servidor  
✅ Lista de utilizadores registados  
✅ Verificação de integridade (AES-GCM)  
✅ Chaves efémeras para forward secrecy  

## Segurança

- **Confidencialidade**: AES-256-GCM
- **Integridade**: AES-GCM (AEAD) + verificação de tag
- **Autenticidade**: Assinaturas ECDSA em todas as mensagens
- **Forward Secrecy**: Chaves efémeras ECDH para cada sessão
- **Servidor não tem acesso**: Às mensagens nem às chaves simétricas

## Limitações

- Comunicação em ambiente local/rede simples
- Sem gestão de revogação de chaves
- Sem persistência de sessões entre reinícios
- Sem proteção contra replay attacks (fora do escopo)
- Sem implementação de protocolo de handshake complexo (TLS, etc.)

## Melhorias Futuras

- Adicionar timestamps e nonces para prevenir replay attacks
- Implementar sistema de revogação de certificados
- Adicionar Perfect Forward Secrecy com renegociação periódica de chaves
- Suporte para comunicação em grupo
- Interface gráfica
- Persistência de histórico de mensagens (cifrado)

## Notas Técnicas

- Utiliza apenas bibliotecas criptográficas seguras e modernas
- Não implementa primitivas criptográficas manualmente
- Separação clara entre camadas: criptografia, rede e lógica de negócio
- Código modular e bem documentado
- Adequado para demonstração em contexto académico

## Licença

Projeto académico desenvolvido para a disciplina de Criptografia Moderna.
