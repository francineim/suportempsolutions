import sqlite3
import os
from datetime import datetime

def conectar():
    """Conecta ao banco de dados SQLite."""
    if not os.path.exists("data"):
        os.makedirs("data")
    
    conn = sqlite3.connect("data/database.db", check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn

def criar_tabelas():
    """Cria todas as tabelas necessárias com migração segura."""
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
                nome_completo TEXT,
                empresa TEXT,
                email TEXT UNIQUE,
                data_cadastro TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                ativo INTEGER DEFAULT 1
            )
        """)
        
        # Tabela de chamados (versão básica primeiro)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS chamados (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                assunto TEXT NOT NULL,
                prioridade TEXT NOT NULL,
                descricao TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'Novo',
                usuario TEXT NOT NULL,
                data_abertura TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                atendente TEXT
            )
        """)
        
        # ========== ADICIONAR COLUNAS NOVAS SE NÃO EXISTIREM ==========
        # Verificar quais colunas já existem
        cursor.execute("PRAGMA table_info(chamados)")
        colunas_existentes = [col[1] for col in cursor.fetchall()]
        
        # Lista de colunas novas para adicionar
        colunas_novas = [
            ("data_inicio_atendimento", "TIMESTAMP"),
            ("data_fim_atendimento", "TIMESTAMP"),
            ("tempo_atendimento_segundos", "INTEGER DEFAULT 0"),
            ("status_atendimento", "TEXT DEFAULT 'nao_iniciado'"),
            ("ultima_retomada", "TIMESTAMP")
        ]
        
        for coluna, tipo in colunas_novas:
            if coluna not in colunas_existentes:
                try:
                    cursor.execute(f"ALTER TABLE chamados ADD COLUMN {coluna} {tipo}")
                    print(f"✅ Coluna '{coluna}' adicionada")
                except Exception as e:
                    print(f"⚠️ Erro ao adicionar coluna '{coluna}': {e}")
        
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
        
        # Tabela de histórico de atendimento (opcional, pode ser criada depois)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS historico_atendimento (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                chamado_id INTEGER NOT NULL,
                acao TEXT NOT NULL,
                data_hora TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                tempo_acumulado_segundos INTEGER,
                atendente TEXT,
                FOREIGN KEY (chamado_id) REFERENCES chamados(id) ON DELETE CASCADE
            )
        """)
        
        # Verificar se admin existe
        cursor.execute("SELECT COUNT(*) FROM usuarios WHERE usuario = 'admin'")
        if cursor.fetchone()[0] == 0:
            cursor.execute(
                "INSERT INTO usuarios (usuario, senha, perfil, nome_completo, empresa, email) VALUES (?, ?, ?, ?, ?, ?)",
                ("admin", "sucodepao", "admin", "Administrador do Sistema", "MP Solutions", "admin@mpsolutions.com.br")
            )
        
        conn.commit()
        print("✅ Tabelas criadas/atualizadas com sucesso")
        return True
        
    except Exception as e:
        print(f"❌ Erro ao criar tabelas: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()

# ========== RESTANTE DO CÓDIGO PERMANECE IGUAL ==========
# [Manter todas as outras funções como estavam na resposta anterior]
