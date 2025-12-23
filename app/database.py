import sqlite3
import streamlit as st
import os

def conectar():
    """Conecta ao banco de dados SQLite."""
    # Verificar se o arquivo do banco existe
    db_path = "database.db"
    
    # Se não existir, criar diretório se necessário
    if not os.path.exists(db_path):
        st.sidebar.info("📁 Criando novo banco de dados...")
    
    conn = sqlite3.connect(db_path, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def criar_tabelas_usuarios():
    """Cria APENAS a tabela de usuários e insere admin."""
    conn = conectar()
    cursor = conn.cursor()
    
    try:
        # Criar tabela de usuários (se não existir)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS usuarios (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                usuario TEXT UNIQUE NOT NULL,
                senha TEXT NOT NULL,
                perfil TEXT NOT NULL,
                data_cadastro TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        conn.commit()
        
        # Verificar se admin existe
        cursor.execute("SELECT COUNT(*) as total FROM usuarios WHERE usuario = 'admin'")
        admin_existe = cursor.fetchone()["total"]
        
        # Criar admin se não existir
        if admin_existe == 0:
            cursor.execute(
                "INSERT INTO usuarios (usuario, senha, perfil) VALUES (?, ?, ?)",
                ("admin", "sucodepao", "admin")
            )
            conn.commit()
            
        # Contar usuários
        cursor.execute("SELECT COUNT(*) as total FROM usuarios")
        total = cursor.fetchone()["total"]
        
        cursor.execute("SELECT usuario, perfil FROM usuarios")
        usuarios = cursor.fetchall()
        
        conn.close()
        
        return {
            "admin_criado": admin_existe == 0,
            "total_usuarios": total,
            "lista_usuarios": [u["usuario"] for u in usuarios]
        }
        
    except Exception as e:
        conn.close()
        return {
            "admin_criado": False,
            "total_usuarios": 0,
            "lista_usuarios": [],
            "erro": str(e)
        }


def criar_tabelas_completas():
    """Cria todas as tabelas do sistema."""
    resultado = criar_tabelas_usuarios()
    
    # Agora criar a tabela de chamados
    conn = conectar()
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS chamados (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                assunto TEXT NOT NULL,
                prioridade TEXT NOT NULL,
                descricao TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'Novo',
                usuario TEXT NOT NULL,
                data_abertura TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        conn.commit()
        conn.close()
        
        return resultado
        
    except Exception as e:
        conn.close()
        resultado["erro"] = str(e)
        return resultado


def verificar_banco():
    """Verifica se o banco de dados está funcional."""
    try:
        conn = conectar()
        cursor = conn.cursor()
        
        # Verificar se tabela usuarios existe
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='usuarios'")
        usuarios_existe = cursor.fetchone() is not None
        
        # Verificar se tabela chamados existe
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='chamados'")
        chamados_existe = cursor.fetchone() is not None
        
        # Listar todas as tabelas
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tabelas = cursor.fetchall()
        
        conn.close()
        
        return {
            "usuarios_existe": usuarios_existe,
            "chamados_existe": chamados_existe,
            "tabelas": [t[0] for t in tabelas]
        }
        
    except Exception as e:
        return {
            "usuarios_existe": False,
            "chamados_existe": False,
            "tabelas": [],
            "erro": str(e)
        }
