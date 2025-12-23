import sqlite3

def conectar():
    """Conecta ao banco de dados SQLite."""
    return sqlite3.connect("database.db", check_same_thread=False)


def verificar_banco():
    """Verifica simplesmente se podemos acessar o banco."""
    try:
        conn = conectar()
        cursor = conn.cursor()
        
        # Tentar contar usuários
        cursor.execute("SELECT COUNT(*) FROM usuarios")
        total = cursor.fetchone()[0]
        
        # Tentar ver colunas (se falhar, estrutura está errada)
        cursor.execute("SELECT usuario, senha, perfil FROM usuarios LIMIT 1")
        
        conn.close()
        return {"status": "ok", "total": total}
        
    except Exception as e:
        return {"status": "error", "message": str(e)}
