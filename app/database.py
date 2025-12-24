# Adicione esta função no início do arquivo, após os imports
def inicializar_pastas():
    """Inicializa todas as pastas necessárias."""
    pastas = ["data", "uploads"]
    
    for pasta in pastas:
        if not os.path.exists(pasta):
            os.makedirs(pasta)
            print(f"📁 Pasta '{pasta}' criada")
    
    return True

# Modifique a função conectar para garantir pastas:
def conectar():
    """Conecta ao banco de dados SQLite."""
    # Garantir que as pastas existam
    inicializar_pastas()
    
    conn = sqlite3.connect("data/database.db", check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn
