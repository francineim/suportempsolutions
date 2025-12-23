import sqlite3

def conectar():
    conn = sqlite3.connect("database.db", check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def criar_tabelas():
    conn = conectar()
    cursor = conn.cursor()

    # Tabela de usuários (adicione esta linha)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS usuarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            usuario TEXT UNIQUE NOT NULL,
            senha TEXT NOT NULL,
            perfil TEXT NOT NULL,
            data_cadastro TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

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

    # Inserir um usuário admin padrão se a tabela estiver vazia
    cursor.execute("SELECT COUNT(*) as count FROM usuarios")
    if cursor.fetchone()["count"] == 0:
        cursor.execute(
            "INSERT INTO usuarios (usuario, senha, perfil) VALUES (?, ?, ?)",
            ("admin", "admin123", "admin")
        )
        st.info("Usuário padrão criado: admin/admin123")

    conn.commit()
    conn.close()
