"""Definições do protocolo de comunicação.

Define os tipos de mensagens e formato JSON para comunicação.
"""

import json
from typing import Dict, Any


class MessageType:
    """Tipos de mensagens do protocolo."""
    # Cliente -> Servidor
    REGISTER = 'REGISTER'
    GET_PUBLIC_KEY = 'GET_PUBLIC_KEY'
    LIST_USERS = 'LIST_USERS'
    
    # Servidor -> Cliente
    REGISTER_OK = 'REGISTER_OK'
    REGISTER_ERROR = 'REGISTER_ERROR'
    PUBLIC_KEY_RESPONSE = 'PUBLIC_KEY_RESPONSE'
    USER_NOT_FOUND = 'USER_NOT_FOUND'
    LIST_USERS_RESPONSE = 'LIST_USERS_RESPONSE'
    ERROR = 'ERROR'
    
    # Cliente -> Cliente (ponto-a-ponto)
    KEY_EXCHANGE = 'KEY_EXCHANGE'
    KEY_EXCHANGE_ACK = 'KEY_EXCHANGE_ACK'
    SECURE_MESSAGE = 'SECURE_MESSAGE'
    MESSAGE_ACK = 'MESSAGE_ACK'


class Protocol:
    """Funções auxiliares para o protocolo."""
    
    @staticmethod
    def create_message(msg_type: str, data: Dict[str, Any]) -> str:
        """Cria mensagem JSON do protocolo.
        
        Args:
            msg_type: Tipo da mensagem
            data: Dados da mensagem
            
        Returns:
            String JSON
        """
        message = {
            'type': msg_type,
            'data': data
        }
        return json.dumps(message)
    
    @staticmethod
    def parse_message(msg_str: str) -> Dict[str, Any]:
        """Parse de mensagem JSON.
        
        Args:
            msg_str: String JSON
            
        Returns:
            Dicionário com 'type' e 'data'
        """
        return json.loads(msg_str)
    
    @staticmethod
    def send_message(sock, message: str):
        """Envia mensagem pelo socket.
        
        Args:
            sock: Socket TCP
            message: String da mensagem
        """
        # Adiciona delimitador de fim de mensagem
        msg_bytes = (message + '\n').encode('utf-8')
        sock.sendall(msg_bytes)
    
    @staticmethod
    def receive_message(sock) -> str:
        """Recebe mensagem do socket.
        
        Args:
            sock: Socket TCP
            
        Returns:
            String da mensagem
        """
        buffer = b''
        while True:
            chunk = sock.recv(1024)
            if not chunk:
                raise ConnectionError("Conexão fechada")
            buffer += chunk
            if b'\n' in buffer:
                break
        
        message = buffer.decode('utf-8').strip()
        return message
