import sqlite3
import streamlit as st

def conectar():
    """Conecta ao banco de dados SQLite."""
    conn = sqlite3.connect("database.db", check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def criar_tabelas():
    """Cria as tabelas do banco de dados e retorna True se admin foi criado."""
    conn = conectar()
    cursor = conn.cursor()
    
    try:
        # 1. Criar tabela de usuários
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS usuarios (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                usuario TEXT UNIQUE NOT NULL,
                senha TEXT NOT NULL,
                perfil TEXT NOT NULL,
                data_cadastro TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # 2. Criar tabela de chamados
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS chamados (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                assunto TEXT NOT NULL,
                prioridade TEXT NOT NULL,
                descricao TEXT NOT NULL,
                status TEXT NOT NULL,
                usuario TEXT NOT NULL,
                data_abertura TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        conn.commit()
        
        # 3. Verificar e criar usuário admin
        admin_criado = False
        
        # Primeiro verificar quantos usuários existem
        cursor.execute("SELECT COUNT(*) as total FROM usuarios")
        total_usuarios = cursor.fetchone()["total"]
        
        # Se não houver usuários ou se admin não existir
        if total_usuarios == 0:
            # Criar admin com senha "sucodepao"
            cursor.execute(
                "INSERT INTO usuarios (usuario, senha, perfil) VALUES (?, ?, ?)",
                ("admin", "sucodepao", "admin")
            )
            conn.commit()
            admin_criado = True
            st.sidebar.info("Usuário admin criado: admin / sucodepao")
        else:
            # Verificar se admin existe especificamente
            cursor.execute("SELECT usuario FROM usuarios WHERE usuario = 'admin'")
            admin_existe = cursor.fetchone()
            
            if not admin_existe:
                # Criar admin mesmo se já houver outros usuários
                cursor.execute(
                    "INSERT INTO usuarios (usuario, senha, perfil) VALUES (?, ?, ?)",
                    ("admin", "sucodepao", "admin")
                )
                conn.commit()
                admin_criado = True
                st.sidebar.info("Usuário admin criado: admin / sucodepao")
        
        # 4. DEBUG: Listar todos os usuários (apenas para depuração)
        cursor.execute("SELECT usuario, perfil FROM usuarios")
        usuarios = cursor.fetchall()
        if usuarios:
            st.sidebar.write(f"Usuários no banco: {[u['usuario'] for u in usuarios]}")
        else:
            st.sidebar.write("Nenhum usuário encontrado no banco")
        
    except Exception as e:
        st.sidebar.error(f"Erro ao criar tabelas: {str(e)}")
        admin_criado = False
    finally:
        conn.close()
    
    return admin_criado
