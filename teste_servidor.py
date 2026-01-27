#!/usr/bin/env python3
"""Script de teste automático do servidor.

Inicia servidor, testa registo de clientes e consultas.
"""

import socket
import json
import time
import subprocess
import sys
import os
import signal

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from comon.primitivas_crypto import CryptoManager
from comon.protocol import MessageType, Protocol


def test_server_connection(host='127.0.0.1', port=5000, max_attempts=5):
    """Testa se o servidor está acessível."""
    for attempt in range(max_attempts):
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(1)
            sock.connect((host, port))
            sock.close()
            return True
        except (ConnectionRefusedError, socket.timeout):
            if attempt < max_attempts - 1:
                time.sleep(1)
    return False


def test_register_client(user_id, host='127.0.0.1', port=5000):
    """Testa registo de um cliente."""
    print(f"\n[*] Testando registo de '{user_id}'...")
    
    crypto = CryptoManager()
    private_key, public_key = crypto.generate_key_pair()
    
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(5)
        sock.connect((host, port))
        
        # Prepara pedido de registo
        public_key_pem = crypto.serialize_public_key(public_key)
        message_to_sign = f"{user_id}:{public_key_pem}".encode('utf-8')
        signature = crypto.sign_message(private_key, message_to_sign)
        
        request = Protocol.create_message(
            MessageType.REGISTER,
            {
                'user_id': user_id,
                'public_key': public_key_pem,
                'signature': signature
            }
        )
        
        Protocol.send_message(sock, request)
        
        # Recebe resposta
        response_str = Protocol.receive_message(sock)
        response = Protocol.parse_message(response_str)
        
        sock.close()
        
        if response['type'] == MessageType.REGISTER_OK:
            print(f"[+] ✓ '{user_id}' registado com sucesso")
            return True, (private_key, public_key)
        else:
            print(f"[-] ✗ Erro no registo: {response['data'].get('message')}")
            return False, None
    
    except Exception as e:
        print(f"[-] ✗ Erro na conexão: {e}")
        return False, None


def test_get_public_key(user_id, host='127.0.0.1', port=5000):
    """Testa consulta de chave pública."""
    print(f"\n[*] Testando consulta de chave pública de '{user_id}'...")
    
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(5)
        sock.connect((host, port))
        
        request = Protocol.create_message(
            MessageType.GET_PUBLIC_KEY,
            {'user_id': user_id}
        )
        
        Protocol.send_message(sock, request)
        
        response_str = Protocol.receive_message(sock)
        response = Protocol.parse_message(response_str)
        
        sock.close()
        
        if response['type'] == MessageType.PUBLIC_KEY_RESPONSE:
            print(f"[+] ✓ Chave pública de '{user_id}' obtida")
            return True, response['data']['public_key']
        else:
            print(f"[-] ✗ {response['data'].get('message')}")
            return False, None
    
    except Exception as e:
        print(f"[-] ✗ Erro na conexão: {e}")
        return False, None


def test_list_users(host='127.0.0.1', port=5000):
    """Testa listagem de utilizadores."""
    print(f"\n[*] Testando listagem de utilizadores...")
    
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(5)
        sock.connect((host, port))
        
        request = Protocol.create_message(MessageType.LIST_USERS, {})
        Protocol.send_message(sock, request)
        
        response_str = Protocol.receive_message(sock)
        response = Protocol.parse_message(response_str)
        
        sock.close()
        
        if response['type'] == MessageType.LIST_USERS_RESPONSE:
            users = response['data']['users']
            print(f"[+] ✓ {len(users)} utilizador(es) registado(s)")
            for user in users:
                print(f"    - {user['user_id']}")
            return True, users
        else:
            print(f"[-] ✗ Erro ao listar utilizadores")
            return False, None
    
    except Exception as e:
        print(f"[-] ✗ Erro na conexão: {e}")
        return False, None


def main():
    """Executa testes do servidor."""
    HOST = '127.0.0.1'
    PORT = 5000
    
    print("="*60)
    print("Teste Automático do Servidor de Registo")
    print("="*60)
    
    # Inicia servidor em background
    print("\n[*] A iniciar servidor...")
    server_process = subprocess.Popen(
        ['python3', 'server/server.py', '--host', HOST, '--port', str(PORT)],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    
    # Aguarda servidor iniciar
    print("[*] A aguardar servidor iniciar...")
    if not test_server_connection(HOST, PORT, max_attempts=10):
        print("[-] ✗ Servidor não iniciou corretamente")
        server_process.terminate()
        return False
    
    print("[+] ✓ Servidor iniciado e acessível\n")
    
    try:
        # Teste 1: Registo de utilizadores
        print("="*60)
        print("Teste 1: Registo de Utilizadores")
        print("="*60)
        
        success_alice, keys_alice = test_register_client('alice', HOST, PORT)
        success_bob, keys_bob = test_register_client('bob', HOST, PORT)
        success_charlie, keys_charlie = test_register_client('charlie', HOST, PORT)
        
        if not (success_alice and success_bob and success_charlie):
            print("\n[-] ✗ Falha no registo de utilizadores")
            return False
        
        # Teste 2: Registo duplicado (deve falhar)
        print("\n" + "="*60)
        print("Teste 2: Registo Duplicado (deve falhar)")
        print("="*60)
        
        success_dup, _ = test_register_client('alice', HOST, PORT)
        if success_dup:
            print("[-] ✗ Registo duplicado não foi rejeitado")
            return False
        else:
            print("[+] ✓ Registo duplicado foi corretamente rejeitado")
        
        # Teste 3: Consulta de chaves públicas
        print("\n" + "="*60)
        print("Teste 3: Consulta de Chaves Públicas")
        print("="*60)
        
        success1, _ = test_get_public_key('alice', HOST, PORT)
        success2, _ = test_get_public_key('bob', HOST, PORT)
        success3, _ = test_get_public_key('charlie', HOST, PORT)
        
        if not (success1 and success2 and success3):
            print("\n[-] ✗ Falha na consulta de chaves")
            return False
        
        # Teste 4: Consulta de utilizador inexistente
        print("\n" + "="*60)
        print("Teste 4: Consulta de Utilizador Inexistente")
        print("="*60)
        
        success_nonexist, _ = test_get_public_key('dave', HOST, PORT)
        if success_nonexist:
            print("[-] ✗ Consulta de utilizador inexistente não retornou erro")
            return False
        else:
            print("[+] ✓ Consulta de utilizador inexistente foi corretamente tratada")
        
        # Teste 5: Listagem de utilizadores
        print("\n" + "="*60)
        print("Teste 5: Listagem de Utilizadores")
        print("="*60)
        
        success_list, users = test_list_users(HOST, PORT)
        if not success_list or len(users) != 3:
            print("[-] ✗ Listagem incorreta")
            return False
        
        print("\n" + "="*60)
        print("✓ TODOS OS TESTES DO SERVIDOR PASSARAM!")
        print("="*60)
        return True
    
    finally:
        # Encerra servidor
        print("\n[*] A encerrar servidor...")
        server_process.terminate()
        server_process.wait(timeout=5)
        print("[+] Servidor encerrado")


if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
