import sqlite3
import bcrypt

def conectar():
    conn = sqlite3.connect("database.db", check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def criar_tabelas():
    """Cria as tabelas do banco de dados e insere um usuário admin padrão se não existir.
    Retorna True se o usuário admin foi criado, False caso contrário.
    """
    conn = conectar()
    cursor = conn.cursor()

    # Tabela de usuários
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS usuarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            usuario TEXT UNIQUE NOT NULL,
            senha_hash TEXT NOT NULL,
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
            status TEXT NOT NULL,
            usuario TEXT NOT NULL,
            data_abertura TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Verificar e criar usuário admin padrão
    cursor.execute("SELECT COUNT(*) as count FROM usuarios")
    admin_criado = False
    if cursor.fetchone()["count"] == 0:
        # Gerar hash da senha
        senha = "sucodepao"
        salt = bcrypt.gensalt()
        senha_hash = bcrypt.hashpw(senha.encode('utf-8'), salt)
        
        cursor.execute(
            "INSERT INTO usuarios (usuario, senha_hash, perfil) VALUES (?, ?, ?)",
            ("admin", senha_hash, "admin")
        )
        admin_criado = True

    conn.commit()
    conn.close()
    return admin_criado


def verificar_senha(senha_digitada, senha_hash_armazenada):
    """Verifica se a senha digitada corresponde ao hash armazenado."""
    return bcrypt.checkpw(senha_digitada.encode('utf-8'), senha_hash_armazenada)
