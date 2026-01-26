# Índice de Ficheiros do Projeto

## Estrutura Completa

```
/app/secure_messaging_system/
│
├── 📁 common/                          # Módulos comuns
│   ├── __init__.py                    # Marcador de pacote Python
│   ├── crypto_primitives.py           # ⭐ Primitivas criptográficas (ECC, ECDH, ECDSA, HKDF, AES-GCM)
│   └── protocol.py                    # Protocolo de comunicação JSON
│
├── 📁 server/                          # Servidor de Registo (AR)
│   ├── __init__.py                    # Marcador de pacote Python
│   ├── database.py                    # Gestão da base de dados SQLite
│   └── server.py                      # ⭐ Servidor principal (Autoridade de Registo)
│
├── 📁 client/                          # Cliente de Mensagens
│   ├── __init__.py                    # Marcador de pacote Python
│   └── client.py                      # ⭐ Cliente CLI interativo
│
├── 📄 test_system.py                   # ⭐ Testes das primitivas criptográficas
├── 📄 test_server.py                   # ⭐ Testes automáticos do servidor
├── 📄 demo.sh                          # Script de demonstração
│
├── 📖 README.md                        # ⭐ Documentação principal
├── 📖 RELATORIO_TECNICO.md             # ⭐ Relatório técnico detalhado (10-15 páginas)
├── 📖 GUIA_RAPIDO.md                   # Guia rápido de utilização
├── 📖 DIAGRAMAS.md                     # Diagramas visuais dos fluxos
└── 📖 INDICE.md                        # Este arquivo
```

## Descrição Detalhada

### 📁 common/ - Módulos Comuns

#### crypto_primitives.py (⭐ CORE)
**Linhas de código**: ~200  
**Propósito**: Implementa todas as operações criptográficas

**Classe Principal**:
- `CryptoManager`: Encapsula todas as primitivas

**Métodos Principais**:
```python
generate_key_pair()         # Gera par ECC SECP256R1
serialize_public_key()      # Serializa chave pública → PEM
deserialize_public_key()    # Deserializa PEM → chave pública
sign_message()              # ECDSA + SHA-256
verify_signature()          # Verifica assinatura ECDSA
perform_ecdh()              # Troca de chaves Diffie-Hellman
derive_key()                # HKDF + SHA-256
encrypt_message()           # AES-256-GCM (cifra)
decrypt_message()           # AES-256-GCM (decifra)
```

**Primitivas Implementadas**:
- ✅ ECC (SECP256R1)
- ✅ ECDH
- ✅ ECDSA + SHA-256
- ✅ HKDF + SHA-256
- ✅ AES-256-GCM
- ✅ SHA-256

#### protocol.py
**Linhas de código**: ~60  
**Propósito**: Define protocolo de comunicação

**Classes**:
- `MessageType`: Tipos de mensagens (REGISTER, GET_PUBLIC_KEY, etc.)
- `Protocol`: Serialização/parsing JSON e envio/receção via socket

---

### 📁 server/ - Autoridade de Registo

#### database.py
**Linhas de código**: ~100  
**Propósito**: Gestão da base de dados SQLite

**Classe**: `Database`

**Métodos**:
```python
init_database()       # Cria tabela users
register_user()       # Regista novo utilizador
get_public_key()      # Consulta chave pública
list_users()          # Lista todos os utilizadores
user_exists()         # Verifica existência
```

**Schema SQLite**:
```sql
CREATE TABLE users (
    user_id TEXT PRIMARY KEY,
    public_key TEXT NOT NULL,
    registration_date TEXT NOT NULL
);
```

#### server.py (⭐ CORE)
**Linhas de código**: ~250  
**Propósito**: Servidor TCP que atua como Autoridade de Registo

**Classe**: `RegistrationAuthority`

**Funcionalidades**:
- Escuta em TCP socket (porta 5000 padrão)
- Multi-threaded (aceita múltiplas conexões)
- Verifica assinaturas digitais nos registos
- Processa pedidos:
  - `REGISTER`: Registo de clientes
  - `GET_PUBLIC_KEY`: Consulta de chave pública
  - `LIST_USERS`: Lista utilizadores

**Execução**:
```bash
python3 server/server.py [--host 127.0.0.1] [--port 5000] [--db caminho.db]
```

---

### 📁 client/ - Cliente de Mensagens

#### client.py (⭐ CORE)
**Linhas de código**: ~450  
**Propósito**: Cliente CLI para mensagens seguras

**Classe**: `SecureClient`

**Funcionalidades**:
1. Geração de par de chaves ECC local
2. Registo no servidor com assinatura digital
3. Consulta de chaves públicas de outros clientes
4. Estabelecimento de sessão segura (ECDH)
5. Derivação de chave de sessão (HKDF)
6. Envio de mensagens cifradas e assinadas
7. Receção e verificação de mensagens
8. Escuta para conexões de entrada (multi-threaded)

**Menu Interativo**:
```
1. Listar utilizadores
2. Estabelecer sessão com peer
3. Enviar mensagem
4. Sair
```

**Execução**:
```bash
python3 client/client.py <user_id> [--server-host 127.0.0.1] [--server-port 5000] [--listen-port 6000]
```

---

### 📄 Scripts de Teste

#### test_system.py (⭐ IMPORTANTE)
**Linhas de código**: ~250  
**Propósito**: Valida todas as primitivas criptográficas

**Testes**:
1. Geração de chaves ECC
2. Serialização/desserialização
3. Assinaturas ECDSA
4. ECDH (troca de chaves)
5. HKDF (derivação)
6. AES-GCM (cifra/decifra)
7. Fluxo completo Alice ↔ Bob

**Execução**:
```bash
python3 test_system.py
```

#### test_server.py
**Linhas de código**: ~200  
**Propósito**: Testa servidor automaticamente

**Testes**:
1. Registo de múltiplos clientes
2. Rejeição de registos duplicados
3. Consulta de chaves públicas
4. Consulta de utilizador inexistente
5. Listagem de utilizadores

**Execução**:
```bash
python3 test_server.py
```

#### demo.sh
**Linhas de código**: ~50  
**Propósito**: Script de demonstração completa

---

### 📖 Documentação

#### README.md (⭐ PRINCIPAL)
**Conteúdo**:
- Descrição do projeto
- Primitivas criptográficas
- Arquitetura (Servidor + Cliente)
- Instruções de instalação
- Guia de utilização passo-a-passo
- Fluxo de estabelecimento de sessão
- Formato das mensagens JSON
- Estrutura do projeto
- Funcionalidades avançadas
- Segurança
- Limitações e melhorias futuras
- Notas técnicas

#### RELATORIO_TECNICO.md (⭐ ACADÉMICO)
**Páginas**: 10-15  
**Conteúdo**:
1. Introdução
2. Arquitetura do Sistema
3. Primitivas Criptográficas (detalhadas)
4. Protocolo de Comunicação
5. Propriedades de Segurança
6. Análise de Segurança
7. Justificação de Escolhas
8. Limitações e Trabalho Futuro
9. Conclusão
10. Referências

**Adequado para**: Entrega académica

#### GUIA_RAPIDO.md
**Conteúdo**:
- Instalação rápida
- Testes rápidos
- Demonstração completa passo-a-passo
- Solução de problemas
- Comandos úteis
- Tabela de primitivas

#### DIAGRAMAS.md
**Conteúdo**:
- Arquitetura geral (ASCII art)
- Fluxo de registo
- Fluxo de estabelecimento de sessão
- Fluxo de envio de mensagem
- Camadas de segurança
- Primitivas e suas funções
- Linha do tempo completa
- Modelo de ameaças e defesas
- Schema da base de dados
- Formato JSON das mensagens

#### INDICE.md
Este arquivo - Índice completo do projeto

---

## Estatísticas do Projeto

### Linhas de Código (aproximado)
```
common/crypto_primitives.py:  ~200 linhas
common/protocol.py:            ~60 linhas
server/database.py:           ~100 linhas
server/server.py:             ~250 linhas
client/client.py:             ~450 linhas
test_system.py:               ~250 linhas
test_server.py:               ~200 linhas
─────────────────────────────────────────
Total:                       ~1510 linhas
```

### Documentação (aproximado)
```
README.md:                    ~250 linhas
RELATORIO_TECNICO.md:         ~400 linhas
GUIA_RAPIDO.md:               ~200 linhas
DIAGRAMAS.md:                 ~450 linhas
─────────────────────────────────────────
Total:                       ~1300 linhas
```

---

## Ficheiros Gerados em Runtime

Durante a execução, o sistema cria:

```
📂 /app/secure_messaging_system/
├── registration_authority.db    # Base de dados SQLite (gerado pelo servidor)
└── __pycache__/                # Cache Python (gerado automaticamente)
    ├── crypto_primitives.*.pyc
    ├── protocol.*.pyc
    ├── database.*.pyc
    └── ...
```

---

## Mapa de Dependências

```
server.py
├── database.py
├── crypto_primitives.py
└── protocol.py

client.py
├── crypto_primitives.py
└── protocol.py

test_system.py
└── crypto_primitives.py

test_server.py
├── crypto_primitives.py
├── protocol.py
└── (inicia server.py como subprocess)
```

---

## Ordem Recomendada de Leitura

Para compreensão do projeto:

1. **README.md** - Visão geral
2. **GUIA_RAPIDO.md** - Como executar
3. **test_system.py** - Executar testes das primitivas
4. **common/crypto_primitives.py** - Ver implementação
5. **DIAGRAMAS.md** - Entender fluxos visualmente
6. **server/server.py** - Servidor
7. **client/client.py** - Cliente
8. **RELATORIO_TECNICO.md** - Análise completa

---

## Ficheiros Essenciais para Demonstração

Se tiver tempo limitado, foque nestes ficheiros:

⭐ **Executáveis**:
1. `test_system.py` - Valida primitivas
2. `test_server.py` - Testa servidor
3. `server/server.py` - Servidor AR
4. `client/client.py` - Cliente CLI

⭐ **Documentação**:
1. `README.md` - Instruções principais
2. `RELATORIO_TECNICO.md` - Relatório académico

---

## Comandos Rápidos

```bash
# Navegar para o projeto
cd /app/secure_messaging_system

# Testar primitivas
python3 test_system.py

# Testar servidor
python3 test_server.py

# Demonstração completa
./demo.sh

# Ver estrutura
tree -L 2
```

---

Este índice fornece uma visão completa de todos os componentes do sistema, facilitando a navegação e compreensão do projeto.
