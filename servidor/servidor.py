#!/usr/bin/env python3
"""Servidor de Registo e Distribuição de Chaves (Autoridade de Registo).

Servidor TCP que:
- Mantém base de dados de utilizadores e chaves públicas
- Permite registo de novos clientes
- Fornece chaves públicas de clientes registados
- Lista utilizadores registados
- Verifica assinaturas digitais
"""

import socket
import sys
import os
import threading
import json

# Adiciona o diretório parent ao path para imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from comon.primitivas_crypto import CryptoManager
from comon.protocol import MessageType, Protocol
from db import Database

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.backends import default_backend

class RegistrationAuthority:
    
    def __init__(self, host: str = '127.0.0.1', port: int = 5000, db_path: str = 'autoridade_registro.db'):
        """
        Args:
            host: Endereço IP do servidor
            port: Porta TCP
            db_path: Caminho para a base de dados
        """
        self.host = host
        self.port = port
        self.db = Database(db_path)
        self.crypto = CryptoManager()
        self.running = False
    
    def handle_client(self, client_socket, client_address):
        """Trata pedidos de um cliente.
        
        Args:
            client_socket: Socket do cliente
            client_address: Endereço do cliente
        """
        print(f"[+] Nova conexão de {client_address}")
        
        try:
            while True:
                # Recebe mensagem
                message_str = Protocol.receive_message(client_socket)
                message = Protocol.parse_message(message_str)
                
                msg_type = message['type']
                data = message['data']
                
                print(f"[*] Recebido {msg_type} de {client_address}")
                
                # Processa pedido
                if msg_type == MessageType.REGISTER:
                    self.handle_register(client_socket, data)
                elif msg_type == MessageType.GET_PUBLIC_KEY:
                    self.handle_get_public_key(client_socket, data)
                elif msg_type == MessageType.LIST_USERS:
                    self.handle_list_users(client_socket)
                else:
                    response = Protocol.create_message(
                        MessageType.ERROR,
                        {'message': 'Tipo de mensagem desconhecido'}
                    )
                    Protocol.send_message(client_socket, response)
        
        except (ConnectionError, json.JSONDecodeError) as e:
            print(f"[-] Erro na conexão com {client_address}: {e}")
        finally:
            client_socket.close()
            print(f"[-] Conexão fechada com {client_address}")
    


    def handle_register(self, client_socket, data):
        """Processa pedido de registo.
        
        Args:
            client_socket: Socket do cliente
            data: Dados do pedido (user_id, public_key, signature)
        """
        print("[DBG] REGISTER data:", data)

        user_id = data.get('user_id')
        public_key_pem = data.get('public_key')
        listen_port = data.get('listen_port')
        signature = data.get('signature')
        
        if not user_id or not public_key_pem or not signature or listen_port is None:
            response = Protocol.create_message(
                MessageType.REGISTER_ERROR,
                {'message': 'Dados incompletos'}
            )
            Protocol.send_message(client_socket, response)
            return
        
        if self.db.user_exists(user_id):
            existing_public_key_pem = self.db.get_public_key(user_id)

            def _pubkey_der(pem_str: str) -> bytes:
                key = serialization.load_pem_public_key(pem_str.encode("utf-8"), backend=default_backend())
                return key.public_bytes(
                    encoding=serialization.Encoding.DER,
                    format=serialization.PublicFormat.SubjectPublicKeyInfo
                )
            
            try:
                if _pubkey_der(existing_public_key_pem) == _pubkey_der(public_key_pem):
                    response = Protocol.create_message(
                        MessageType.REGISTER_OK,
                        {'message': 'Utilizador já registado (chave confirmada)'}
                    )
                    Protocol.send_message(client_socket, response)
                    return
            except Exception:
                # fallback (se houver lixo/encoding inesperado na BD)
                if (existing_public_key_pem or "").strip() == public_key_pem.strip():
                    response = Protocol.create_message(
                        MessageType.REGISTER_OK,
                        {'message': 'Utilizador já registado (chave confirmada)'}
                    )
                    Protocol.send_message(client_socket, response)
                    return

            response = Protocol.create_message(
                MessageType.REGISTER_ERROR,
                {'message': 'Utilizador já registado com chave pública diferente'}
            )
            Protocol.send_message(client_socket, response)
            return
        
        # Verifica assinatura digital do pedido
        try:
            public_key = self.crypto.deserialize_public_key(public_key_pem)
            message_to_verify = f"{user_id}:{public_key_pem}".encode('utf-8')
            
            if not self.crypto.verify_signature(public_key, message_to_verify, signature):
                response = Protocol.create_message(
                    MessageType.REGISTER_ERROR,
                    {'message': 'Assinatura inválida'}
                )
                Protocol.send_message(client_socket, response)
                return
        except Exception as e:
            response = Protocol.create_message(
                MessageType.REGISTER_ERROR,
                {'message': f'Erro ao verificar assinatura: {str(e)}'}
            )
            Protocol.send_message(client_socket, response)
            return
        
        # Regista utilizador
        if self.db.register_user(user_id, public_key_pem, listen_port):
            print(f"[+] Utilizador '{user_id}' registado com sucesso")
            response = Protocol.create_message(
                MessageType.REGISTER_OK,
                {'message': 'Registo efetuado com sucesso'}
            )
        else:
            response = Protocol.create_message(
                MessageType.REGISTER_ERROR,
                {'message': 'Erro ao registar utilizador'}
            )
        
        Protocol.send_message(client_socket, response)
    
    def handle_get_public_key(self, client_socket, data):
        """Processa pedido de chave pública.
        
        Args:
            client_socket: Socket do cliente
            data: Dados do pedido (user_id)
        """
        user_id = data.get('user_id')
        
        if not user_id:
            response = Protocol.create_message(
                MessageType.ERROR,
                {'message': 'user_id não fornecido'}
            )
            Protocol.send_message(client_socket, response)
            return
        
        public_key = self.db.get_public_key(user_id)
        
        if public_key:
            response = Protocol.create_message(
                MessageType.PUBLIC_KEY_RESPONSE,
                {'user_id': user_id, 'public_key': public_key}
            )
        else:
            response = Protocol.create_message(
                MessageType.USER_NOT_FOUND,
                {'message': f"Utilizador '{user_id}' não encontrado"}
            )
        
        Protocol.send_message(client_socket, response)
    
    def handle_list_users(self, client_socket):
        """Lista todos os utilizadores registados.
        
        Args:
            client_socket: Socket do cliente
        """
        
        users = self.db.list_users()
        users_list = [{'user_id': uid, 'registration_date': date, 'listen_port': port} for uid, date, port in users]
        
        response = Protocol.create_message(
            MessageType.LIST_USERS_RESPONSE,
            {'users': users_list}
        )
        Protocol.send_message(client_socket, response)
    
    def start(self):
        """Inicia o servidor."""
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        
        try:
            server_socket.bind((self.host, self.port))
            server_socket.listen(5)
            self.running = True
            
            print(f"[*] Servidor de Registo iniciado em {self.host}:{self.port}")
            print(f"[*] Base de dados: {self.db.db_path}")
            print(f"[*] A aguardar conexões...\n")
            
            while self.running:
                client_socket, client_address = server_socket.accept()
                client_thread = threading.Thread(
                    target=self.handle_client,
                    args=(client_socket, client_address)
                )
                client_thread.daemon = True
                client_thread.start()
        
        except KeyboardInterrupt:
            print("\n[*] Servidor a encerrar...")
        finally:
            server_socket.close()
            print("[*] Servidor encerrado")

def main():
    """Função principal."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Servidor de Registo (Autoridade de Registo)')
    parser.add_argument('--host', default='127.0.0.1', help='Endereço IP (default: 127.0.0.1)')
    parser.add_argument('--port', type=int, default=5000, help='Porta TCP (default: 5000)')
    parser.add_argument('--db', default='autoridade_registro.db', help='Caminho da base de dados')
    
    args = parser.parse_args()
    
    server = RegistrationAuthority(args.host, args.port, args.db)
    server.start()

if __name__ == '__main__':
    main()
