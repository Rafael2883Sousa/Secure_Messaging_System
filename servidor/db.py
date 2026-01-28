"""Módulo de gestão da base de dados SQLite.

Gere o armazenamento de utilizadores registados e suas chaves públicas.
"""

import sqlite3
import datetime
from typing import Optional, List, Tuple
import os


class Database:
    """Gestor da base de dados SQLite."""
    
    def __init__(self, db_path: str = 'autoridade_registro.db'):
        """
        Args:
            db_path: Caminho para o ficheiro da base de dados
        """
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """Cria a tabela de utilizadores se não existir."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                user_id TEXT PRIMARY KEY,
                listen_port INTEGER,
                public_key TEXT NOT NULL,
                registration_date TEXT NOT NULL
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def register_user(self, user_id: str, public_key: str, listen_port: int) -> bool:
        """Regista um novo utilizador.
        
        Args:
            user_id: ID do utilizador
            public_key: Chave pública em formato PEM
            listen_port: porta a escutar
            
        Returns:
            True se registado com sucesso
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            registration_date = datetime.datetime.now().isoformat()
            
            cursor.execute(
                'INSERT INTO users (user_id, listen_port, public_key, registration_date) VALUES (?, ?, ?, ?)',
                (user_id, listen_port, public_key, registration_date)
            )
            
            conn.commit()
            conn.close()
            return True
        except sqlite3.IntegrityError:
            return False
    
    def get_public_key(self, user_id: str) -> Optional[str]:
        """Obtém a chave pública de um utilizador.
        
        Args:
            user_id: ID do utilizador
            
        Returns:
            Chave pública em formato PEM, ou None se não existir
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('SELECT public_key FROM users WHERE user_id = ?', (user_id,))
        result = cursor.fetchone()
        
        conn.close()
        
        return result[0] if result else None
    
    def list_users(self) -> List[Tuple[str, str]]:
        """Lista todos os utilizadores registados.
        
        Returns:
            Lista de tuplas (user_id, registration_date)
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('SELECT user_id, listen_port, registration_date FROM users ORDER BY registration_date')
        results = cursor.fetchall()
        
        conn.close()
        
        return results
    
    def user_exists(self, user_id: str) -> bool:
        """Verifica se um utilizador existe.
        
        Args:
            user_id: ID do utilizador
            
        Returns:
            True se existe, False caso contrário
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('SELECT 1 FROM users WHERE user_id = ?', (user_id,))
        result = cursor.fetchone()
        
        conn.close()
        
        return result is not None
