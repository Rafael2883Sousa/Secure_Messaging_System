# Índice de Ficheiros do Projeto

## Estrutura Completa

```
/app/secure_messaging_system/
│
├── 📁 common/                        # Módulos comuns
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

### 📁 comon/ - Módulos Comuns

#### primitivas_crypto.py
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
**Propósito**: Define protocolo de comunicação

**Classes**:
- `MessageType`: Tipos de mensagens (REGISTER, GET_PUBLIC_KEY, etc.)
- `Protocol`: Serialização/parsing JSON e envio/receção via socket

---

### 📁 servidor/ - Autoridade de Registo

#### db.py
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

#### servidor.py
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

### 📁 cliente/ - Cliente de Mensagens

#### client.py
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

#### teste_systema.py 
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
python3 teste_systema.py
```

#### teste_servidor.py
**Propósito**: Testa servidor automaticamente

**Testes**:
1. Registo de múltiplos clientes
2. Rejeição de registos duplicados
3. Consulta de chaves públicas
4. Consulta de utilizador inexistente
5. Listagem de utilizadores

**Execução**:
```bash
python3 teste_servidor.py
```

### 📖 Documentação

#### README.md 
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

#### RELATORIO_TECNICO.md 
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

#### GUIA.md
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

## Ficheiros Gerados em Runtime

Durante a execução, o sistema cria:

```
📂 /app/secure_messaging_system/
├── autoridade_registro.db    # Base de dados SQLite (gerado pelo servidor)
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
├── db.py
├── primitivas_crypto.py
└── protocol.py

cliente.py
├── primitivas_crypto.py
└── protocol.py

teste_systema.py
└── primitivas_crypto.py

teste_servidor.py
├── primitivas_crypto.py
├── protocol.py
└── (inicia server.py como subprocess)
```

---

## Ordem Recomendada de Leitura

Para compreensão do projeto:

1. **README.md** - Visão geral
2. **GUIA_RAPIDO.md** - Como executar
3. **teste_systema.py** - Executar testes das primitivas
4. **comon/primitivas_crypto.py** - Ver implementação
5. **DIAGRAMAS.md** - Entender fluxos visualmente
6. **servidor/servidor.py** - Servidor
7. **cliente/cliente.py** - Cliente
8. **RELATORIO_TECNICO.md** - Análise completa

---

## Ficheiros Essenciais para Demonstração

⭐ **Executáveis**:
1. `teste_systema.py` - Valida primitivas
2. `teste_servidor.py` - Testa servidor
3. `servidor/servidor.py` - Servidor AR
4. `cliente/client.py` - Cliente CLI

⭐ **Documentação**:
1. `README.md` - Instruções principais
2. `RELATORIO_TECNICO.md` - Relatório académico

---

## Comandos Rápidos

```bash
# Navegar para o projeto
cd /app/secure_messaging_system

# Testar primitivas
python3 teste_systema.py

# Testar servidor
python3 teste_servidor.py

# Demonstração completa
./demo.sh

# Ver estrutura
tree -L 2
```

---
Este índice fornece uma visão completa de todos os componentes do sistema, facilitando a navegação e compreensão do projeto.
