#!/usr/bin/env python3
"""Script de teste para validar o sistema de mensagens seguras.

Testa:
1. Geração de chaves
2. Assinaturas digitais
3. ECDH
4. HKDF
5. AES-GCM
6. Fluxo completo
"""

import sys
import os

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from common.crypto_primitives import CryptoManager


def test_key_generation():
    """Teste de geração de chaves ECC."""
    print("[*] Teste 1: Geração de chaves ECC (SECP256R1)")
    crypto = CryptoManager()
    
    private_key, public_key = crypto.generate_key_pair()
    assert private_key is not None
    assert public_key is not None
    
    print("[+] Chaves geradas com sucesso")
    print(f"    - Chave privada: {type(private_key).__name__}")
    print(f"    - Chave pública: {type(public_key).__name__}")
    
    return crypto, private_key, public_key


def test_serialization(crypto, private_key, public_key):
    """Teste de serialização de chaves."""
    print("\n[*] Teste 2: Serialização e desserialização de chaves")
    
    # Serializa
    public_pem = crypto.serialize_public_key(public_key)
    private_pem = crypto.serialize_private_key(private_key)
    
    print(f"[+] Chave pública serializada ({len(public_pem)} bytes)")
    print(f"[+] Chave privada serializada ({len(private_pem)} bytes)")
    
    # Desserializa
    public_key_recovered = crypto.deserialize_public_key(public_pem)
    private_key_recovered = crypto.deserialize_private_key(private_pem)
    
    assert public_key_recovered is not None
    assert private_key_recovered is not None
    
    print("[+] Chaves desserializadas com sucesso")


def test_signatures(crypto, private_key, public_key):
    """Teste de assinaturas digitais ECDSA."""
    print("\n[*] Teste 3: Assinaturas digitais (ECDSA + SHA-256)")
    
    message = b"Esta e uma mensagem de teste"
    
    # Assina
    signature = crypto.sign_message(private_key, message)
    print(f"[+] Mensagem assinada ({len(signature)} bytes base64)")
    
    # Verifica assinatura válida
    is_valid = crypto.verify_signature(public_key, message, signature)
    assert is_valid
    print("[+] Assinatura verificada com sucesso")
    
    # Verifica assinatura inválida
    tampered_message = b"Mensagem alterada"
    is_valid = crypto.verify_signature(public_key, tampered_message, signature)
    assert not is_valid
    print("[+] Assinatura inválida detectada corretamente")


def test_ecdh(crypto):
    """Teste de ECDH."""
    print("\n[*] Teste 4: ECDH (troca de chaves)")
    
    # Alice gera par de chaves
    alice_private, alice_public = crypto.generate_key_pair()
    print("[+] Alice gerou suas chaves")
    
    # Bob gera par de chaves
    bob_private, bob_public = crypto.generate_key_pair()
    print("[+] Bob gerou suas chaves")
    
    # Alice calcula segredo partilhado
    alice_shared = crypto.perform_ecdh(alice_private, bob_public)
    print(f"[+] Alice calculou segredo partilhado ({len(alice_shared)} bytes)")
    
    # Bob calcula segredo partilhado
    bob_shared = crypto.perform_ecdh(bob_private, alice_public)
    print(f"[+] Bob calculou segredo partilhado ({len(bob_shared)} bytes)")
    
    # Verifica se são iguais
    assert alice_shared == bob_shared
    print("[+] Segredos partilhados são iguais! ✓")
    
    return alice_shared


def test_hkdf(crypto, shared_secret):
    """Teste de derivação de chaves com HKDF."""
    print("\n[*] Teste 5: HKDF (derivação de chave)")
    
    session_key = crypto.derive_key(shared_secret)
    assert len(session_key) == 32  # AES-256
    
    print(f"[+] Chave de sessão derivada ({len(session_key)} bytes)")
    print("[+] Chave AES-256 pronta para uso")
    
    return session_key


def test_aes_gcm(crypto, session_key):
    """Teste de cifra AES-GCM."""
    print("\n[*] Teste 6: AES-256-GCM (cifra simétrica)")
    
    plaintext = b"Mensagem secreta a ser cifrada!"
    print(f"[+] Plaintext: '{plaintext.decode()}'")
    
    # Cifra
    encrypted = crypto.encrypt_message(session_key, plaintext)
    print(f"[+] Mensagem cifrada:")
    print(f"    - Nonce: {len(encrypted['nonce'])} bytes (base64)")
    print(f"    - Ciphertext: {len(encrypted['ciphertext'])} bytes (base64)")
    print(f"    - Tag: {len(encrypted['tag'])} bytes (base64)")
    
    # Decifra
    decrypted = crypto.decrypt_message(
        session_key,
        encrypted['nonce'],
        encrypted['ciphertext'],
        encrypted['tag']
    )
    
    assert decrypted == plaintext
    print(f"[+] Mensagem decifrada: '{decrypted.decode()}'")
    print("[+] Confidencialidade e integridade verificadas! ✓")


def test_full_flow():
    """Teste do fluxo completo."""
    print("\n" + "="*60)
    print("TESTE DE FLUXO COMPLETO - Comunicação Alice ↔ Bob")
    print("="*60)
    
    crypto = CryptoManager()
    
    # 1. Alice e Bob geram chaves
    print("\n[1] Geração de chaves")
    alice_private, alice_public = crypto.generate_key_pair()
    bob_private, bob_public = crypto.generate_key_pair()
    print("    ✓ Alice e Bob geraram pares de chaves ECC")
    
    # 2. Troca de chaves públicas (simulando servidor)
    print("\n[2] Troca de chaves públicas (via servidor)")
    alice_public_pem = crypto.serialize_public_key(alice_public)
    bob_public_pem = crypto.serialize_public_key(bob_public)
    print("    ✓ Chaves públicas serializadas")
    
    # 3. Estabelecimento de sessão (ECDH)
    print("\n[3] Estabelecimento de sessão segura (ECDH)")
    alice_ephemeral_priv, alice_ephemeral_pub = crypto.generate_key_pair()
    bob_ephemeral_priv, bob_ephemeral_pub = crypto.generate_key_pair()
    
    alice_shared = crypto.perform_ecdh(alice_ephemeral_priv, bob_ephemeral_pub)
    bob_shared = crypto.perform_ecdh(bob_ephemeral_priv, alice_ephemeral_pub)
    
    assert alice_shared == bob_shared
    print("    ✓ ECDH executado com sucesso")
    
    # 4. Derivação de chave de sessão (HKDF)
    print("\n[4] Derivação de chave de sessão (HKDF)")
    alice_session_key = crypto.derive_key(alice_shared)
    bob_session_key = crypto.derive_key(bob_shared)
    
    assert alice_session_key == bob_session_key
    print("    ✓ Chaves de sessão derivadas e iguais")
    
    # 5. Alice envia mensagem cifrada e assinada
    print("\n[5] Alice → Bob: Mensagem cifrada e assinada")
    message = b"Ola Bob! Esta mensagem e confidencial e autenticada."
    
    # Cifra
    encrypted = crypto.encrypt_message(alice_session_key, message)
    
    # Assina o ciphertext
    ciphertext_bytes = encrypted['ciphertext'].encode('utf-8')
    signature = crypto.sign_message(alice_private, ciphertext_bytes)
    encrypted['signature'] = signature
    
    print(f"    ✓ Mensagem cifrada com AES-GCM")
    print(f"    ✓ Ciphertext assinado com ECDSA")
    
    # 6. Bob recebe e processa
    print("\n[6] Bob recebe e processa mensagem")
    
    # Verifica assinatura
    ciphertext_received = encrypted['ciphertext'].encode('utf-8')
    alice_public_recovered = crypto.deserialize_public_key(alice_public_pem)
    
    is_valid = crypto.verify_signature(
        alice_public_recovered,
        ciphertext_received,
        encrypted['signature']
    )
    assert is_valid
    print("    ✓ Assinatura verificada (autenticidade)")
    
    # Decifra
    decrypted = crypto.decrypt_message(
        bob_session_key,
        encrypted['nonce'],
        encrypted['ciphertext'],
        encrypted['tag']
    )
    assert decrypted == message
    print("    ✓ Mensagem decifrada (confidencialidade)")
    print(f"    ✓ Integridade verificada (GCM tag)")
    print(f"\n    Mensagem recebida: '{decrypted.decode()}'")
    
    print("\n" + "="*60)
    print("✓ TODOS OS TESTES PASSARAM COM SUCESSO!")
    print("="*60)


def main():
    """Executa todos os testes."""
    try:
        # Testes individuais
        crypto, private_key, public_key = test_key_generation()
        test_serialization(crypto, private_key, public_key)
        test_signatures(crypto, private_key, public_key)
        shared_secret = test_ecdh(crypto)
        session_key = test_hkdf(crypto, shared_secret)
        test_aes_gcm(crypto, session_key)
        
        # Teste de fluxo completo
        test_full_flow()
        
        print("\n" + "="*60)
        print("RESUMO DAS PRIMITIVAS TESTADAS:")
        print("="*60)
        print("✓ ECC (SECP256R1) - Geração de chaves")
        print("✓ ECDH - Troca de chaves")
        print("✓ ECDSA + SHA-256 - Assinaturas digitais")
        print("✓ HKDF + SHA-256 - Derivação de chaves")
        print("✓ AES-256-GCM - Cifra autenticada (AEAD)")
        print("✓ SHA-256 - Função hash")
        print("="*60)
        print("\n[+] Sistema validado e pronto para uso!")
        
    except Exception as e:
        print(f"\n[-] ERRO: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
