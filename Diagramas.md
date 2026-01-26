# Diagramas do Sistema

## 1. Arquitetura Geral

```
┌─────────────────────────────────────────────────────────────────┐
│                     Sistema de Mensagens Seguras                │
└─────────────────────────────────────────────────────────────────┘

┌─────────────┐                                      ┌─────────────┐
│  Cliente A  │                                      │  Cliente B  │
│   (Alice)   │                                      │    (Bob)    │
├─────────────┤                                      ├─────────────┤
│ • Par ECC   │                                      │ • Par ECC   │
│ • Listen    │                                      │ • Listen    │
│   port 6000 │                                      │   port 6001 │
└──────┬──────┘                                      └──────┬──────┘
       │                                                    │
       │                 ┌──────────────┐                   │
       ├────────────────►│   Servidor   │◄──────────────────┤
       │                 │     (AR)     │                   │
       │                 ├──────────────┤                   │
       │                 │ • Port 5000  │                   │
       │                 │ • SQLite DB  │                   │
       │                 │ • Verifica   │                   │
       │                 │   assinaturas│                   │
       │                 └──────────────┘                   │
       │                                                    │
       │         Após obter chaves públicas via AR          │
       │                                                    │
       │   ┌─────────────────────────────────────────┐      │
       └──►│    Sessão Segura Ponto-a-Ponto (P2P)   │◄──────┘
           │    • ECDH para chave de sessão          │
           │    • AES-GCM para mensagens             │
           │    • ECDSA para assinaturas             │
           └─────────────────────────────────────────┘
```

## 2. Fluxo de Registo

```
Cliente                               Servidor (AR)
  │                                       │
  │ 1. Gera par ECC (priv, pub)           │
  │    usando SECP256R1                   │
  │                                       │
  │ 2. Cria mensagem:                     │
  │    msg = "user_id:public_key_pem"     │
  │                                       │
  │ 3. Assina com ECDSA:                  │
  │    sig = sign(priv, msg)              │
  │                                       │
  │ 4. REGISTER                           │
  ├───────────────────────────────────────►
  │    {user_id, public_key, signature}    │
  │                                        │
  │                         5. Deserializa public_key
  │                                        │
  │                         6. Reconstrói mensagem
  │                            msg = "user_id:public_key_pem"
  │                                        │
  │                         7. Verifica assinatura
  │                            verify(public_key, msg, sig)
  │                                        │
  │                         8. Se válida:  │
  │                            INSERT INTO users
  │                            VALUES (user_id, public_key, timestamp)
  │                                        │
  │                    REGISTER_OK         │
  │◄───────────────────────────────────────┤
  │                                        │
  │ 9. Registo completo                    │
  │                                        │
```

## 3. Fluxo de Estabelecimento de Sessão

```
Alice                  Servidor (AR)                  Bob
  │                         │                          │
  │ 1. GET_PUBLIC_KEY       │                          │
  ├────────────────────────►│                          │
  │    {user_id: "bob"}     │                          │
  │                         │                          │
  │  PUBLIC_KEY_RESPONSE    │                          │
  │◄────────────────────────┤                          │
  │  {bob, public_key_pem}  │                          │
  │                         │                          │
  │ 2. Gera chave efémera ECDH                         │
  │    (a, A) onde A = a·G  │                          │
  │                         │                          │
  │ 3. Conecta diretamente a Bob (P2P)                 │
  │                         │                          │
  │              KEY_EXCHANGE                          │
  ├────────────────────────────────────────────────────►
  │              {from: alice,                         │
  │               ephemeral_public_key: A}             │
  │                         │                          │
  │                         │         4. Recebe pedido │
  │                         │            Gera (b, B)   │
  │                         │            onde B = b·G  │
  │                         │                          │
  │            KEY_EXCHANGE_ACK                        │
  │◄───────────────────────────────────────────────────┤
  │            {ephemeral_public_key: B}               │
  │                         │                          │
  │ 5. ECDH:                │              6. ECDH:    │
  │    S = a·B              │                 S = b·A  │
  │                         │                          │
  │    (a·B = a·b·G)        │         (b·A = b·a·G)    │
  │                         │                          │
  │ 7. HKDF:                │              8. HKDF:    │
  │    K = HKDF(S)          │                 K = HKDF(S)
  │                         │                          │
  │ ✓ Ambos possuem a mesma chave de sessão K         │
  │                         │                          │
  │ ═══════════════════════════════════════════════════│
  │     Sessão segura estabelecida (AES-GCM com K)     │
  │ ═══════════════════════════════════════════════════│
```

## 4. Fluxo de Envio de Mensagem

```
Alice                                                   Bob
  │                                                     │
  │ 1. Mensagem plaintext M                             │
  │    M = "Olá Bob!"                                   │
  │                                                     │
  │ 2. Cifra com AES-256-GCM usando chave K:            │
  │    (nonce, ciphertext, tag) = AES-GCM(K, M)         │
  │                                                     │
  │ 3. Assina o ciphertext com ECDSA:                   │
  │    signature = sign(priv_Alice, ciphertext)         │
  │                                                     │
  │ 4. SECURE_MESSAGE                                   │
  ├─────────────────────────────────────────────────────►
  │    {from: alice,                                    │
  │     encrypted_data: {                               │
  │       nonce: "...",                                 │
  │       ciphertext: "...",                            │
  │       tag: "...",                                   │
  │       signature: "..."                              │
  │     }}                                              │
  │                                                     │
  │                         5. Obtém public_key_Alice   │
  │                            (da cache ou servidor)   │
  │                                                     │
  │                         6. Verifica assinatura:     │
  │                            verify(pub_Alice,        │
  │                                    ciphertext,      │
  │                                    signature)       │
  │                            ✓ Autenticidade          │
  │                                                     │
  │                         7. Decifra com AES-GCM:     │
  │                            M = decrypt(K,           │
  │                                       nonce,        │
  │                                       ciphertext,   │
  │                                       tag)          │
  │                            ✓ Confidencialidade      │
  │                            ✓ Integridade (tag)      │
  │                                                     │
  │                         8. Exibe mensagem:          │
  │                            [alice]: Olá Bob!        │
  │                                                     │
```

## 5. Camadas de Segurança

```
┌─────────────────────────────────────────────────────────┐
│                    Mensagem Original                    │
│                   "Olá Bob, tudo bem?"                  │
└─────────────────────────────────────────────────────────┘
                          │
                          ▼
┌────────────────────────────────────────────────────────┐
│          Camada 1: Cifra Simétrica (AES-256-GCM)       │
│  ┌────────────────────────────────────────────────┐    │
│  │ Plaintext → AES-GCM(K) → Ciphertext + Tag      │    │
│  │ • Confidencialidade: Apenas quem tem K decifra │    │
│  │ • Integridade: Tag verifica modificações       │    │
│  └────────────────────────────────────────────────┘    │
└────────────────────────────────────────────────────────┘
                          │
                          ▼
┌────────────────────────────────────────────────────────┐
│       Camada 2: Assinatura Digital (ECDSA + SHA-256)   │
│  ┌────────────────────────────────────────────────┐    │
│  │ Ciphertext → ECDSA(priv_Alice) → Signature     │    │
│  │ • Autenticidade: Prova que Alice enviou        │    │
│  │ • Não-repúdio: Alice não pode negar            │    │
│  └────────────────────────────────────────────────┘    │
└────────────────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────┐
│                  Mensagem Transmitida                   │
│     {nonce, ciphertext, tag, signature} em JSON         │
└─────────────────────────────────────────────────────────┘
```

## 6. Primitivas Criptográficas e suas Funções

```
┌──────────────────────────────────────────────────────────┐
│                  ECC (SECP256R1)                         │
│  Curva elíptica para criptografia de chave pública       │
│  ┌──────────────────────────────────────────────────┐    │
│  │ • Geração de pares de chaves (priv, pub)         │    │
│  │ • Base para ECDH e ECDSA                         │    │
│  │ • Segurança: ~128 bits (equivalente RSA-3072)    │    │
│  └──────────────────────────────────────────────────┘    │
└──────────────────────────────────────────────────────────┘
                           │
         ┌─────────────────┴─────────────────┐
         ▼                                   ▼
┌──────────────────────┐        ┌──────────────────────┐
│   ECDH               │        │   ECDSA              │
│   Troca de Chaves    │        │   Assinatura Digital │
├──────────────────────┤        ├──────────────────────┤
│ • Alice: S = a·B     │        │ • Assina mensagem    │
│ • Bob:   S = b·A     │        │ • Verifica origem    │
│ • S = a·b·G (igual)  │        │ • SHA-256 para hash  │
└──────────────────────┘        └──────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────────────┐
│              HKDF (SHA-256)                         │
│              Derivação de Chave                     │
│  ┌──────────────────────────────────────────┐       │
│  │ Shared Secret (S) → HKDF → Session Key   │       │
│  │ • Extract: PRK = HMAC(salt, S)           │       │
│  │ • Expand: K = HMAC(PRK, info)            │       │
│  │ • Output: 32 bytes (AES-256)             │       │
│  └──────────────────────────────────────────┘       │
└─────────────────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────────────┐
│              AES-256-GCM                            │
│              Cifra Simétrica Autenticada            │
│  ┌──────────────────────────────────────────┐       │
│  │ Plaintext + Key (K) → Ciphertext + Tag   │       │
│  │ • AES-256: 256-bit key                   │       │
│  │ • GCM: Galois/Counter Mode (AEAD)        │       │
│  │ • Nonce: 96 bits (aleatório)             │       │
│  │ • Tag: 128 bits (autenticação)           │       │
│  └──────────────────────────────────────────┘       │
└─────────────────────────────────────────────────────┘
```

## 7. Linha do Tempo de uma Comunicação Completa

```
Tempo │ Alice                    Servidor (AR)              Bob
──────┼─────────────────────────────────────────────────────────
  T0  │ Inicia aplicação        │                          │
      │ Gera par ECC            │                          │
      │                         │                          │
  T1  │ REGISTER ──────────────►│                          │
      │                         │ Verifica assinatura      │
      │                         │ Armazena em SQLite       │
      │ ◄────────── REGISTER_OK │                          │
      │                         │                          │
  T2  │                         │                          Inicia
      │                         │                          Gera par ECC
      │                         │                          │
  T3  │                         │ ◄────────── REGISTER     │
      │                         │             (Bob)        │
      │                         │ Verifica e armazena      │
      │                         │ ────────────► OK         │
      │                         │                          │
  T4  │ GET_PUBLIC_KEY(bob) ───►│                          │
      │ ◄─────── public_key_bob │                          │
      │                         │                          │
  T5  │ Gera chave efémera      │                          │
      │ KEY_EXCHANGE ───────────────────────────────────►  │
      │                         │                   Gera efémera
      │ ◄────────────────────── KEY_EXCHANGE_ACK ─────────  │
      │                         │                          │
  T6  │ ECDH → Shared Secret    │         Shared Secret ← ECDH
      │ HKDF → Session Key (K)  │         Session Key (K) ← HKDF
      │                         │                          │
      │ ═════════════════ Sessão Segura Estabelecida ═════════
      │                         │                          │
  T7  │ Mensagem M              │                          │
      │ AES-GCM(K, M) → C       │                          │
      │ ECDSA(priv, C) → sig    │                          │
      │ SECURE_MESSAGE(C, sig) ─────────────────────────►  │
      │                         │               Verifica sig
      │                         │               Decifra C→M
      │                         │               Exibe M
      │                         │                          │
  T8  │                         │          Mensagem resposta
      │                         │          AES-GCM(K, M2)→C2
      │ ◄──────────────────────── SECURE_MESSAGE(C2, sig2) │
      │ Verifica e decifra      │                          │
      │ Exibe M2                │                          │
      │                         │                          │
```

## 8. Modelo de Ameaças e Defesas

```
┌────────────────────────────────────────────────────────────┐
│                    Ameaça: Escuta Passiva                  │
│  Atacante captura tráfego e tenta ler mensagens            │
│  ┌──────────────────────────────────────────────────┐      │
│  │ Defesa: AES-256-GCM                              │      │
│  │ • Tráfego cifrado com chave de 256 bits          │      │
│  │ • Atacante vê apenas ciphertext em base64        │      │
│  │ • Sem chave de sessão, não pode decifrar         │      │
│  └──────────────────────────────────────────────────┘      │
└────────────────────────────────────────────────────────────┘

┌────────────────────────────────────────────────────────────┐
│               Ameaça: Man-in-the-Middle (MITM)             │
│  Atacante intercepta e modifica mensagens                  │
│  ┌──────────────────────────────────────────────────┐      │
│  │ Defesa: GCM Tag + Assinatura ECDSA               │      │
│  │ • GCM tag detecta modificação do ciphertext      │      │
│  │ • Assinatura ECDSA vincula mensagem ao remetente │      │
│  │ • Atacante não pode forjar assinatura            │      │
│  └──────────────────────────────────────────────────┘      │
└────────────────────────────────────────────────────────────┘

┌────────────────────────────────────────────────────────────┐
│                  Ameaça: Personificação                    │
│  Atacante tenta passar-se por Alice                        │
│  ┌──────────────────────────────────────────────────┐      │
│  │ Defesa: Assinaturas ECDSA                        │      │
│  │ • Cada mensagem assinada com chave privada       │      │
│  │ • Apenas Alice possui sua chave privada          │      │
│  │ • Bob verifica com chave pública de Alice        │      │
│  └──────────────────────────────────────────────────┘      │
└────────────────────────────────────────────────────────────┘

┌────────────────────────────────────────────────────────────┐
│           Ameaça: Comprometimento de Sessão Passada        │
│  Chave privada de Alice é roubada no futuro                │
│  ┌──────────────────────────────────────────────────┐      │
│  │ Defesa: Forward Secrecy (Chaves Efémeras ECDH)   │      │
│  │ • Cada sessão usa par efémero único              │      │
│  │ • Chaves efémeras descartadas após sessão        │      │
│  │ • Comprometimento futuro não afeta passado       │      │
│  └──────────────────────────────────────────────────┘      │
└────────────────────────────────────────────────────────────┘
```

## 9. Base de Dados SQLite

```
┌────────────────────────────────────────────────────────┐
│          Tabela: users                                 │
├──────────────┬─────────────────────────────────────────┤
│ user_id      │ TEXT PRIMARY KEY                        │
│ public_key   │ TEXT NOT NULL (formato PEM)             │
│ registration_│ TEXT NOT NULL (ISO 8601 timestamp)      │
│ date         │                                         │
└──────────────┴─────────────────────────────────────────┘

Exemplo de registos:

┌──────────┬────────────────────────┬────────────────────────┐
│ user_id  │ public_key (resumido)  │ registration_date      │
├──────────┼────────────────────────┼────────────────────────┤
│ alice    │ -----BEGIN PUBLIC...   │ 2025-01-08T14:30:00    │
│ bob      │ -----BEGIN PUBLIC...   │ 2025-01-08T14:31:15    │
│ charlie  │ -----BEGIN PUBLIC...   │ 2025-01-08T14:32:45    │
└──────────┴────────────────────────┴────────────────────────┘

Operações:
• INSERT: Registo de novo utilizador (com verificação de assinatura)
• SELECT: Consulta de chave pública por user_id
• SELECT: Listagem de todos os utilizadores
```

## 10. Formato JSON das Mensagens

### Registo (Cliente → Servidor)
```json
{
  "type": "REGISTER",
  "data": {
    "user_id": "alice",
    "public_key": "-----BEGIN PUBLIC KEY-----\nMFkwEw...\n-----END PUBLIC KEY-----\n",
    "signature": "MEUCIQDx3V..."
  }
}
```

### Resposta de Registo (Servidor → Cliente)
```json
{
  "type": "REGISTER_OK",
  "data": {
    "message": "Registo efetuado com sucesso"
  }
}
```

### Troca de Chaves (Cliente → Cliente)
```json
{
  "type": "KEY_EXCHANGE",
  "data": {
    "from": "alice",
    "ephemeral_public_key": "-----BEGIN PUBLIC KEY-----\n..."
  }
}
```

### Mensagem Segura (Cliente → Cliente)
```json
{
  "type": "SECURE_MESSAGE",
  "data": {
    "from": "alice",
    "encrypted_data": {
      "nonce": "dGVzdG5vbmNl",
      "ciphertext": "Y2lwaGVydGV4dA==",
      "tag": "dGFn",
      "signature": "MEUCIQC..."
    }
  }
}
```

---

Estes diagramas fornecem uma visão visual completa do sistema, facilitando a compreensão dos fluxos e mecanismos de segurança implementados.
