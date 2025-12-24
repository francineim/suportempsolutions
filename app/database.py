import sqlite3
import os

def conectar():
    """Conecta ao banco de dados SQLite."""
    # Garantir que a pasta data existe
    if not os.path.exists("data"):
        os.makedirs("data")
    
    conn = sqlite3.connect("data/database.db", check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn

def criar_tabelas():
    """Cria todas as tabelas necessárias."""
    conn = conectar()
    cursor = conn.cursor()
    
    try:
        # Tabela de usuários
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS usuarios (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                usuario TEXT UNIQUE NOT NULL,
                senha TEXT NOT NULL,
                perfil TEXT NOT NULL,
                data_cadastro TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Tabela de chamados
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS chamados (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                assunto TEXT NOT NULL,
                prioridade TEXT NOT NULL,
                descricao TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'Novo',
                usuario TEXT NOT NULL,
                data_abertura TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                data_atendimento TIMESTAMP,
                data_fechamento TIMESTAMP,
                atendente TEXT
            )
        """)
        
        # Tabela de anexos
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS anexos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                chamado_id INTEGER NOT NULL,
                nome_arquivo TEXT NOT NULL,
                caminho_arquivo TEXT NOT NULL,
                data_upload TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (chamado_id) REFERENCES chamados(id) ON DELETE CASCADE
            )
        """)
        
        # Verificar se admin existe
        cursor.execute("SELECT COUNT(*) FROM usuarios WHERE usuario = 'admin'")
        if cursor.fetchone()[0] == 0:
            cursor.execute(
                "INSERT INTO usuarios (usuario, senha, perfil) VALUES (?, ?, ?)",
                ("admin", "sucodepao", "admin")
            )
        
        conn.commit()
        return True
        
    except Exception as e:
        print(f"Erro ao criar tabelas: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()

def buscar_chamados(usuario=None, perfil=None):
    """Busca chamados baseado no perfil."""
    conn = conectar()
    cursor = conn.cursor()
    
    try:
        if perfil == "admin":
            cursor.execute("""
                SELECT id, assunto, prioridade, status, data_abertura, usuario, atendente
                FROM chamados
                ORDER BY data_abertura DESC
            """)
        else:
            cursor.execute("""
                SELECT id, assunto, prioridade, status, data_abertura, usuario, atendente
                FROM chamados
                WHERE usuario = ?
                ORDER BY data_abertura DESC
            """, (usuario,))
        
        return cursor.fetchall()
    finally:
        conn.close()

def buscar_descricao_chamado(chamado_id):
    """Busca a descrição completa de um chamado."""
    conn = conectar()
    cursor = conn.cursor()
    
    try:
        cursor.execute("SELECT descricao FROM chamados WHERE id = ?", (chamado_id,))
        resultado = cursor.fetchone()
        return resultado["descricao"] if resultado else ""
    finally:
        conn.close()

def salvar_anexo(chamado_id, nome_arquivo, caminho_arquivo):
    """Salva um anexo no banco de dados."""
    conn = conectar()
    cursor = conn.cursor()
    
    try:
        cursor.execute(
            "INSERT INTO anexos (chamado_id, nome_arquivo, caminho_arquivo) VALUES (?, ?, ?)",
            (chamado_id, nome_arquivo, caminho_arquivo)
        )
        conn.commit()
        return True
    except Exception as e:
        conn.rollback()
        print(f"Erro ao salvar anexo: {e}")
        return False
    finally:
        conn.close()

def buscar_anexos(chamado_id):
    """Busca anexos de um chamado."""
    conn = conectar()
    cursor = conn.cursor()
    
    try:
        cursor.execute(
            "SELECT id, nome_arquivo, data_upload, caminho_arquivo FROM anexos WHERE chamado_id = ? ORDER BY data_upload DESC",
            (chamado_id,)
        )
        return cursor.fetchall()
    finally:
        conn.close()
