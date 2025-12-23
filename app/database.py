import sqlite3
import os

def conectar():
    """Conecta ao banco de dados SQLite de forma SIMPLES."""
    return sqlite3.connect("database.db", check_same_thread=False)


def criar_banco_se_nao_existir():
    """Cria o banco de dados apenas se não existir."""
    if not os.path.exists("database.db"):
        conn = conectar()
        cursor = conn.cursor()
        
        # Criar tabela de usuários (SEMPRE 'senha', NUNCA 'senha_hash')
        cursor.execute("""
            CREATE TABLE usuarios (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                usuario TEXT UNIQUE NOT NULL,
                senha TEXT NOT NULL,
                perfil TEXT NOT NULL,
                data_cadastro TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Criar tabela de chamados
        cursor.execute("""
            CREATE TABLE chamados (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                assunto TEXT NOT NULL,
                prioridade TEXT NOT NULL,
                descricao TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'Novo',
                usuario TEXT NOT NULL,
                data_abertura TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Inserir admin padrão
        cursor.execute(
            "INSERT INTO usuarios (usuario, senha, perfil) VALUES (?, ?, ?)",
            ("admin", "sucodepao", "admin")
        )
        
        conn.commit()
        conn.close()
        return True
    return False


def verificar_estrutura():
    """Verifica se a estrutura do banco está correta."""
    conn = conectar()
    cursor = conn.cursor()
    
    try:
        # Verificar se a tabela usuarios existe e tem coluna 'senha'
        cursor.execute("PRAGMA table_info(usuarios)")
        colunas = cursor.fetchall()
        
        if not colunas:
            return {"status": "error", "message": "Tabela 'usuarios' não existe"}
        
        colunas_nomes = [col[1] for col in colunas]
        
        if 'senha' not in colunas_nomes:
            return {"status": "error", "message": f"Coluna 'senha' não encontrada. Colunas existentes: {colunas_nomes}"}
        
        # Contar usuários
        cursor.execute("SELECT COUNT(*) as total FROM usuarios")
        total = cursor.fetchone()[0]
        
        return {
            "status": "ok",
            "colunas": colunas_nomes,
            "total_usuarios": total
        }
        
    except Exception as e:
        return {"status": "error", "message": str(e)}
    finally:
        conn.close()
