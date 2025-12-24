import sqlite3
import os

def conectar():
    """Conecta ao banco de dados SQLite."""
    # Garantir que a pasta data existe
    if not os.path.exists("data"):
        os.makedirs("data")
        print("📁 Pasta 'data' criada")
    
    try:
        conn = sqlite3.connect("data/database.db", check_same_thread=False)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        return conn
    except Exception as e:
        print(f"❌ ERRO AO CONECTAR: {e}")
        raise

def criar_tabelas():
    """Cria todas as tabelas necessárias."""
    conn = None
    try:
        conn = conectar()
        cursor = conn.cursor()
        
        print("🔧 Criando tabelas...")
        
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
        print("✅ Tabela 'usuarios' verificada")
        
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
        print("✅ Tabela 'chamados' verificada")
        
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
        print("✅ Tabela 'anexos' verificada")
        
        # Verificar se admin existe
        cursor.execute("SELECT COUNT(*) FROM usuarios WHERE usuario = 'admin'")
        if cursor.fetchone()[0] == 0:
            cursor.execute(
                "INSERT INTO usuarios (usuario, senha, perfil) VALUES (?, ?, ?)",
                ("admin", "sucodepao", "admin")
            )
            print("✅ Usuário 'admin' criado")
        
        conn.commit()
        print("✅ Todas as tabelas verificadas/criadas")
        return True
        
    except Exception as e:
        print(f"❌ ERRO AO CRIAR TABELAS: {e}")
        if conn:
            conn.rollback()
        return False
    finally:
        if conn:
            conn.close()
