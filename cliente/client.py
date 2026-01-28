#!/usr/bin/env python3
"""Cliente de Mensagens Seguras.

Cliente CLI que:
- Gera par de chaves ECC localmente
- Regista-se no servidor
- Solicita chaves públicas de outros clientes
- Estabelece sessões seguras ponto-a-ponto
- Troca mensagens cifradas e assinadas
"""

import socket
import sys
import os
import json
import threading
import time

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from comon.primitivas_crypto import CryptoManager
from comon.protocol import MessageType, Protocol


class SecureClient:
    """Cliente de mensagens seguras."""
    
    def __init__(self, user_id: str, server_host: str = '127.0.0.1', server_port: int = 5000):
        """Inicializa o cliente.
        
        Args:
            user_id: ID do utilizador
            server_host: Endereço do servidor de registo
            server_port: Porta do servidor de registo
        """
        self.user_id = user_id
        self.server_host = server_host
        self.server_port = server_port
        self.crypto = CryptoManager()
        
        # Par de chaves do cliente
        self.private_key = None
        self.public_key = None
        
        # Sessões ativas
        self.sessions = {}  # {peer_id: {'key': session_key, 'peer_public_key': ...}}
        
        # Estado de escuta para mensagens recebidas
        self.listening = False
        self.listen_socket = None
        self.listen_port = None
    
    def generate_keys(self):
        """Gera par de chaves ECC local."""
        print("[*] A gerar par de chaves ECC (SECP256R1)...")
        self.private_key, self.public_key = self.crypto.generate_key_pair()
        print("[+] Par de chaves gerado com sucesso")
    
    def load_or_generate_keys(self):
        """
        Carrega chaves do disco se existirem; caso contrário gera e guarda.
        Isto evita alterar a identidade (user_id -> public_key) entre execuções.
        """
        keys_dir = os.path.join(os.path.dirname(__file__), "keys")
        os.makedirs(keys_dir, exist_ok=True)

        priv_path = os.path.join(keys_dir, f"{self.user_id}_private.pem")
        pub_path = os.path.join(keys_dir, f"{self.user_id}_public.pem")

        if os.path.exists(priv_path) and os.path.exists(pub_path):
            # Carregar
            with open(priv_path, "r", encoding="utf-8") as f:
                priv_pem = f.read()
            with open(pub_path, "r", encoding="utf-8") as f:
                pub_pem = f.read()

            self.private_key = self.crypto.deserialize_private_key(priv_pem)
            self.public_key = self.crypto.deserialize_public_key(pub_pem)

            print(f"[+] Chaves carregadas do disco: {priv_path} / {pub_path}")
            return

        # Gerar e guardar
        print("[*] Nenhuma chave encontrada. A gerar novo par ECC (SECP256R1)...")
        self.private_key, self.public_key = self.crypto.generate_key_pair()

        priv_pem = self.crypto.serialize_private_key(self.private_key)  
        pub_pem = self.crypto.serialize_public_key(self.public_key)

        with open(priv_path, "w", encoding="utf-8") as f:
            f.write(priv_pem)
        with open(pub_path, "w", encoding="utf-8") as f:
            f.write(pub_pem)

        print(f"[+] Chaves geradas e guardadas: {priv_path} / {pub_path}")

    def register_with_server(self) -> bool:
        """Regista o cliente no servidor.
        
        Returns:
            True se registado com sucesso
        """
        if not self.private_key or not self.public_key:
            print("[-] Erro: Par de chaves não gerado")
            return False
        
        print(f"[*] A registar utilizador '{self.user_id}' no servidor...")
        
        try:
            # Conecta ao servidor
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.connect((self.server_host, self.server_port))
            
            # Serializa chave pública
            public_key_pem = self.crypto.serialize_public_key(self.public_key)
            
            # Assina o pedido de registo
            message_to_sign = f"{self.user_id}:{public_key_pem}".encode('utf-8')
            signature = self.crypto.sign_message(self.private_key, message_to_sign)
            
            # Envia pedido de registo
            request = Protocol.create_message(
                MessageType.REGISTER,
                {
                    'user_id': self.user_id,
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
                print(f"[+] Registo efetuado com sucesso!")
                return True
            else:
                print(f"[-] Erro no registo: {response['data'].get('message')}")
                return False
        
        except Exception as e:
            print(f"[-] Erro ao registar: {e}")
            return False
    
    def get_peer_public_key(self, peer_id: str) -> str:
        """Obtém a chave pública de outro cliente.
        
        Args:
            peer_id: ID do peer
            
        Returns:
            Chave pública PEM do peer, ou None
        """
        print(f"[*] A solicitar chave pública de '{peer_id}'...")
        
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.connect((self.server_host, self.server_port))
            
            request = Protocol.create_message(
                MessageType.GET_PUBLIC_KEY,
                {'user_id': peer_id}
            )
            Protocol.send_message(sock, request)
            
            response_str = Protocol.receive_message(sock)
            response = Protocol.parse_message(response_str)
            
            sock.close()
            
            if response['type'] == MessageType.PUBLIC_KEY_RESPONSE:
                print(f"[+] Chave pública de '{peer_id}' obtida")
                return response['data']['public_key']
            else:
                print(f"[-] {response['data'].get('message')}")
                return None
        
        except Exception as e:
            print(f"[-] Erro ao obter chave pública: {e}")
            return None
    
    def list_users(self):
        """Lista todos os utilizadores registados."""
        print("[*] A solicitar lista de utilizadores...")
        
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.connect((self.server_host, self.server_port))
            
            request = Protocol.create_message(MessageType.LIST_USERS, {})
            Protocol.send_message(sock, request)
            
            response_str = Protocol.receive_message(sock)
            response = Protocol.parse_message(response_str)
            
            sock.close()
            
            if response['type'] == MessageType.LIST_USERS_RESPONSE:
                users = response['data']['users']
                print("\n=== Utilizadores Registados ===")
                for user in users:
                    print(f"  - {user['user_id']} (registado em {user['registration_date']})")
                print("================================\n")
            else:
                print(f"[-] Erro: {response['data'].get('message')}")
        
        except Exception as e:
            print(f"[-] Erro ao listar utilizadores: {e}")
    
    def establish_session(self, peer_id: str, peer_host: str, peer_port: int) -> bool:
        """Estabelece sessão segura com outro cliente usando ECDH.
        
        Args:
            peer_id: ID do peer
            peer_host: Endereço IP do peer
            peer_port: Porta do peer
            
        Returns:
            True se sessão estabelecida com sucesso
        """
        print(f"[*] A estabelecer sessão segura com '{peer_id}'...")
        
        # Obtém chave pública do peer do servidor
        peer_public_key_pem = self.get_peer_public_key(peer_id)
        if not peer_public_key_pem:
            return False
        
        peer_public_key = self.crypto.deserialize_public_key(peer_public_key_pem)
        
        try:
            # Conecta ao peer
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.connect((peer_host, peer_port))
            
            # Gera chave efémera para ECDH
            ephemeral_private, ephemeral_public = self.crypto.generate_key_pair()
            ephemeral_public_pem = self.crypto.serialize_public_key(ephemeral_public)
            
            # Envia chave efémera ao peer
            key_exchange = Protocol.create_message(
                MessageType.KEY_EXCHANGE,
                {
                    'from': self.user_id,
                    'ephemeral_public_key': ephemeral_public_pem
                }
            )
            Protocol.send_message(sock, key_exchange)
            
            # Recebe chave efémera do peer
            response_str = Protocol.receive_message(sock)
            response = Protocol.parse_message(response_str)
            
            if response['type'] != MessageType.KEY_EXCHANGE_ACK:
                print("[-] Erro no estabelecimento da sessão")
                sock.close()
                return False
            
            peer_ephemeral_pem = response['data']['ephemeral_public_key']
            peer_ephemeral_public = self.crypto.deserialize_public_key(peer_ephemeral_pem)
            
            # Realiza ECDH
            shared_secret = self.crypto.perform_ecdh(ephemeral_private, peer_ephemeral_public)
            
            # Deriva chave de sessão
            session_key = self.crypto.derive_key(shared_secret)
            
            # Armazena sessão
            self.sessions[peer_id] = {
                'key': session_key,
                'peer_public_key': peer_public_key,
                'socket': sock
            }
            
            print(f"[+] Sessão segura estabelecida com '{peer_id}'")
            print(f"[+] Chave de sessão derivada via HKDF + SHA-256")
            return True
        
        except Exception as e:
            print(f"[-] Erro ao estabelecer sessão: {e}")
            return False
    
    def send_secure_message(self, peer_id: str, message: str) -> bool:
        """Envia mensagem cifrada e assinada.
        
        Args:
            peer_id: ID do destinatário
            message: Mensagem em texto claro
            
        Returns:
            True se enviada com sucesso
        """
        if peer_id not in self.sessions:
            print(f"[-] Sessão com '{peer_id}' não estabelecida")
            return False
        
        session = self.sessions[peer_id]
        session_key = session['key']
        sock = session['socket']
        
        try:
            # Cifra mensagem com AES-GCM
            plaintext = message.encode('utf-8')
            encrypted = self.crypto.encrypt_message(session_key, plaintext)
            
            # Assina o ciphertext com ECDSA
            ciphertext_bytes = encrypted['ciphertext'].encode('utf-8')
            signature = self.crypto.sign_message(self.private_key, ciphertext_bytes)
            
            # Adiciona assinatura
            encrypted['signature'] = signature
            
            # Envia mensagem segura
            secure_msg = Protocol.create_message(
                MessageType.SECURE_MESSAGE,
                {
                    'from': self.user_id,
                    'encrypted_data': encrypted
                }
            )
            Protocol.send_message(sock, secure_msg)
            
            print(f"[+] Mensagem enviada para '{peer_id}' (cifrada e assinada)")
            return True
        
        except Exception as e:
            print(f"[-] Erro ao enviar mensagem: {e}")
            return False
    
    def start_listening(self, port: int = 0):
        """Inicia escuta para conexões de entrada.
        
        Args:
            port: Porta para escutar (0 = porta aleatória)
        """
        self.listen_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.listen_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.listen_socket.bind(('0.0.0.0', port))
        self.listen_socket.listen(5)
        
        self.listen_port = self.listen_socket.getsockname()[1]
        self.listening = True
        
        print(f"[*] A escutar em 0.0.0.0:{self.listen_port}")
        
        listen_thread = threading.Thread(target=self._listen_loop)
        listen_thread.daemon = True
        listen_thread.start()
    
    def _listen_loop(self):
        """Loop de escuta para conexões de entrada."""
        while self.listening:
            try:
                client_socket, client_address = self.listen_socket.accept()
                print(f"[+] Conexão recebida de {client_address}")
                
                handle_thread = threading.Thread(
                    target=self._handle_incoming,
                    args=(client_socket,)
                )
                handle_thread.daemon = True
                handle_thread.start()
            except Exception as e:
                if self.listening:
                    print(f"[-] Erro na escuta: {e}")
    
    def _handle_incoming(self, client_socket):
        """Trata conexões de entrada.
        
        Args:
            client_socket: Socket do peer
        """
        try:
            # Recebe troca de chaves
            message_str = Protocol.receive_message(client_socket)
            message = Protocol.parse_message(message_str)
            
            if message['type'] == MessageType.KEY_EXCHANGE:
                peer_id = message['data']['from']
                peer_ephemeral_pem = message['data']['ephemeral_public_key']
                
                print(f"[*] Pedido de sessão de '{peer_id}'")
                
                # Obtém chave pública permanente do peer
                peer_public_key_pem = self.get_peer_public_key(peer_id)
                if not peer_public_key_pem:
                    client_socket.close()
                    return
                
                peer_public_key = self.crypto.deserialize_public_key(peer_public_key_pem)
                peer_ephemeral_public = self.crypto.deserialize_public_key(peer_ephemeral_pem)
                
                # Gera própria chave efémera
                ephemeral_private, ephemeral_public = self.crypto.generate_key_pair()
                ephemeral_public_pem = self.crypto.serialize_public_key(ephemeral_public)
                
                # Envia resposta
                ack = Protocol.create_message(
                    MessageType.KEY_EXCHANGE_ACK,
                    {'ephemeral_public_key': ephemeral_public_pem}
                )
                Protocol.send_message(client_socket, ack)
                
                # Realiza ECDH
                shared_secret = self.crypto.perform_ecdh(ephemeral_private, peer_ephemeral_public)
                session_key = self.crypto.derive_key(shared_secret)
                
                # Armazena sessão
                self.sessions[peer_id] = {
                    'key': session_key,
                    'peer_public_key': peer_public_key,
                    'socket': client_socket
                }
                
                print(f"[+] Sessão estabelecida com '{peer_id}'")
                
                # Continua a escutar mensagens desta sessão
                self._receive_messages(peer_id, client_socket)
            
        except Exception as e:
            print(f"[-] Erro ao tratar conexão: {e}")
            client_socket.close()
    
    def _receive_messages(self, peer_id: str, sock):
        """Recebe mensagens de uma sessão ativa.
        
        Args:
            peer_id: ID do peer
            sock: Socket da sessão
        """
        session = self.sessions.get(peer_id)
        if not session:
            return
        
        session_key = session['key']
        peer_public_key = session['peer_public_key']
        
        try:
            while True:
                message_str = Protocol.receive_message(sock)
                message = Protocol.parse_message(message_str)
                
                if message['type'] == MessageType.SECURE_MESSAGE:
                    encrypted_data = message['data']['encrypted_data']
                    sender = message['data']['from']
                    
                    # Verifica assinatura
                    ciphertext_bytes = encrypted_data['ciphertext'].encode('utf-8')
                    signature = encrypted_data['signature']
                    
                    if not self.crypto.verify_signature(peer_public_key, ciphertext_bytes, signature):
                        print(f"[-] Assinatura inválida de '{sender}'")
                        continue
                    
                    # Decifra mensagem
                    plaintext = self.crypto.decrypt_message(
                        session_key,
                        encrypted_data['nonce'],
                        encrypted_data['ciphertext'],
                        encrypted_data['tag']
                    )
                    
                    print(f"\n[{sender}]: {plaintext.decode('utf-8')}")
        
        except Exception as e:
            print(f"[-] Sessão com '{peer_id}' encerrada: {e}")
            if peer_id in self.sessions:
                del self.sessions[peer_id]


def main():
    """Função principal - Interface CLI."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Cliente de Mensagens Seguras')
    parser.add_argument('user_id', help='ID do utilizador')
    parser.add_argument('--server-host', default='127.0.0.1', help='Endereço do servidor')
    parser.add_argument('--server-port', type=int, default=5000, help='Porta do servidor')
    parser.add_argument('--listen-port', type=int, default=0, help='Porta para escutar')
    
    args = parser.parse_args()
    
    client = SecureClient(args.user_id, args.server_host, args.server_port)
    
    # Gera chaves
    client.load_or_generate_keys()
    
    # Regista no servidor
    if not client.register_with_server():
        print("[-] Falha no registo. A sair.")
        return
    
    # Inicia escuta
    client.start_listening(args.listen_port)
    print(f"\n[*] Cliente '{args.user_id}' pronto!")
    print(f"[*] Porta de escuta: {client.listen_port}\n")
    
    # # Menu interativo
    # print("=== Menu ===")
    # print("1. Listar utilizadores")
    # print("2. Estabelecer sessão com peer")
    # print("3. Enviar mensagem")
    # print("4. Sair")
    # print("============\n")
    
    while True:
        try:
            choice = input(f"Escolha uma opção: \n=== Menu ===\n1. Listar utilizadores\n2. Estabelecer sessão com peer\n3. Enviar mensagem\n4. Sair\n============\n").strip()
            
            if choice == '1':
                client.list_users()
            
            elif choice == '2':
                peer_id = input("ID do peer: ").strip()
                peer_host = input("Endereço do peer: ").strip()
                peer_port = int(input("Porta do peer: ").strip())
                client.establish_session(peer_id, peer_host, peer_port)
            
            elif choice == '3':
                peer_id = input("ID do destinatário: ").strip()
                message = input("Mensagem: ").strip()
                client.send_secure_message(peer_id, message)
            
            elif choice == '4':
                print("[*] A sair...")
                break
            
            else:
                print("[-] Opção inválida")
        
        except KeyboardInterrupt:
            print("\n[*] A sair...")
            break
        except Exception as e:
            print(f"[-] Erro: {e}")


if __name__ == '__main__':
    main()
