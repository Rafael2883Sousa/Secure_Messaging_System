"""Módulo de primitivas criptográficas.

Implementa todas as operações criptográficas necessárias usando a biblioteca cryptography:
- ECC (SECP256R1)
- ECDH para troca de chaves
- ECDSA + SHA-256 para assinaturas digitais
- HKDF + SHA-256 para derivação de chaves
- AES-256-GCM (AEAD)
"""

import os
import base64
from typing import Tuple, Dict

from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.kdf.hkdf import HKDF
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.backends import default_backend


class CryptoManager:
    """Gestor de operações criptográficas."""
    
    def __init__(self):
        self.backend = default_backend()
        self.curve = ec.SECP256R1()
    
    def generate_key_pair(self) -> Tuple[ec.EllipticCurvePrivateKey, ec.EllipticCurvePublicKey]:
        """Gera um par de chaves ECC (SECP256R1).
        
        Returns:
            Tupla (chave_privada, chave_publica)
        """
        private_key = ec.generate_private_key(self.curve, self.backend)
        public_key = private_key.public_key()
        return private_key, public_key
    
    def serialize_public_key(self, public_key: ec.EllipticCurvePublicKey) -> str:
        """Serializa chave pública para formato PEM (base64).
        
        Args:
            public_key: Chave pública ECC
            
        Returns:
            String base64 da chave pública
        """
        pem = public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        )
        return pem.decode('utf-8')
    
    def deserialize_public_key(self, pem_str: str) -> ec.EllipticCurvePublicKey:
        """Deserializa chave pública do formato PEM.
        
        Args:
            pem_str: String PEM da chave pública
            
        Returns:
            Chave pública ECC
        """
        return serialization.load_pem_public_key(
            pem_str.encode('utf-8'),
            backend=self.backend
        )
    
    def serialize_private_key(self, private_key: ec.EllipticCurvePrivateKey, password: bytes = None) -> str:
        """Serializa chave privada para formato PEM.
        
        Args:
            private_key: Chave privada ECC
            password: Opcional, password para encriptar a chave
            
        Returns:
            String PEM da chave privada
        """
        encryption = serialization.NoEncryption()
        if password:
            encryption = serialization.BestAvailableEncryption(password)
        
        pem = private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=encryption
        )
        return pem.decode('utf-8')
    
    def deserialize_private_key(self, pem_str: str, password: bytes = None) -> ec.EllipticCurvePrivateKey:
        """Deserializa chave privada do formato PEM.
        
        Args:
            pem_str: String PEM da chave privada
            password: Opcional, password se a chave estiver encriptada
            
        Returns:
            Chave privada ECC
        """
        return serialization.load_pem_private_key(
            pem_str.encode('utf-8'),
            password=password,
            backend=self.backend
        )
    
    def sign_message(self, private_key: ec.EllipticCurvePrivateKey, message: bytes) -> str:
        """Assina uma mensagem com ECDSA + SHA-256.
        
        Args:
            private_key: Chave privada do signatário
            message: Mensagem a assinar
            
        Returns:
            Assinatura em base64
        """
        signature = private_key.sign(
            message,
            ec.ECDSA(hashes.SHA256())
        )
        return base64.b64encode(signature).decode('utf-8')
    
    def verify_signature(self, public_key: ec.EllipticCurvePublicKey, message: bytes, signature: str) -> bool:
        """Verifica uma assinatura ECDSA.
        
        Args:
            public_key: Chave pública do signatário
            message: Mensagem original
            signature: Assinatura em base64
            
        Returns:
            True se a assinatura é válida, False caso contrário
        """
        try:
            signature_bytes = base64.b64decode(signature)
            public_key.verify(
                signature_bytes,
                message,
                ec.ECDSA(hashes.SHA256())
            )
            return True
        except Exception:
            return False
    
    def perform_ecdh(self, private_key: ec.EllipticCurvePrivateKey, peer_public_key: ec.EllipticCurvePublicKey) -> bytes:
        """Realiza troca de chaves ECDH.
        
        Args:
            private_key: Chave privada local
            peer_public_key: Chave pública do peer
            
        Returns:
            Segredo partilhado (bytes)
        """
        shared_key = private_key.exchange(ec.ECDH(), peer_public_key)
        return shared_key
    
    def derive_key(self, shared_secret: bytes, salt: bytes = b'', info: bytes = b'session_key') -> bytes:
        """Deriva chave de sessão usando HKDF + SHA-256.
        
        Args:
            shared_secret: Segredo partilhado do ECDH
            salt: Salt (usar vazio ou mesmo valor em ambos os lados)
            info: Informação contextual
            
        Returns:
            Chave AES-256 (32 bytes)
        """
        hkdf = HKDF(
            algorithm=hashes.SHA256(),
            length=32,  # AES-256
            salt=salt,
            info=info,
            backend=self.backend
        )
        return hkdf.derive(shared_secret)
    
    def encrypt_message(self, key: bytes, plaintext: bytes) -> Dict[str, str]:
        """Cifra mensagem com AES-256-GCM.
        
        Args:
            key: Chave AES-256 (32 bytes)
            plaintext: Mensagem a cifrar
            
        Returns:
            Dicionário com nonce, ciphertext e tag em base64
        """
        aesgcm = AESGCM(key)
        nonce = os.urandom(12)  # 96 bits para GCM
        
        # AES-GCM retorna ciphertext + tag concatenados
        ciphertext = aesgcm.encrypt(nonce, plaintext, None)
        
        # Separar ciphertext e tag (últimos 16 bytes são o tag)
        actual_ciphertext = ciphertext[:-16]
        tag = ciphertext[-16:]
        
        return {
            'nonce': base64.b64encode(nonce).decode('utf-8'),
            'ciphertext': base64.b64encode(actual_ciphertext).decode('utf-8'),
            'tag': base64.b64encode(tag).decode('utf-8')
        }
    
    def decrypt_message(self, key: bytes, nonce: str, ciphertext: str, tag: str) -> bytes:
        """Decifra mensagem AES-256-GCM.
        
        Args:
            key: Chave AES-256 (32 bytes)
            nonce: Nonce em base64
            ciphertext: Ciphertext em base64
            tag: Tag de autenticação em base64
            
        Returns:
            Plaintext (bytes)
            
        Raises:
            Exception: Se a verificação de integridade falhar
        """
        aesgcm = AESGCM(key)
        nonce_bytes = base64.b64decode(nonce)
        ciphertext_bytes = base64.b64decode(ciphertext)
        tag_bytes = base64.b64decode(tag)
        
        # AES-GCM espera ciphertext + tag concatenados
        combined = ciphertext_bytes + tag_bytes
        
        plaintext = aesgcm.decrypt(nonce_bytes, combined, None)
        return plaintext
