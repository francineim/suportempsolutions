import sqlite3
import bcrypt

def conectar():
    conn = sqlite3.connect("database.db", check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def criar_tabelas():
    """Cria as tabelas do banco de dados de forma segura."""
    conn = conectar()
    cursor = conn.cursor()
    
    # 1. Primeiro criar tabelas se não existirem (estrutura básica)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS usuarios_temp (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            usuario TEXT UNIQUE NOT NULL,
            senha_hash TEXT NOT NULL,
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
    
    # 2. Verificar se a tabela usuarios existe e tem a estrutura correta
    try:
        cursor.execute("PRAGMA table_info(usuarios)")
        colunas = cursor.fetchall()
        
        if colunas:  # Tabela existe
            # Verificar se tem coluna senha_hash
            colunas_nomes = [col[1] for col in colunas]
            
            if 'senha_hash' not in colunas_nomes:
                # Estrutura antiga - vamos criar nova tabela
                print("Estrutura antiga detectada, migrando...")
                
                # Criar nova tabela com estrutura correta
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS usuarios_nova (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        usuario TEXT UNIQUE NOT NULL,
                        senha_hash TEXT NOT NULL,
                        perfil TEXT NOT NULL,
                        data_cadastro TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                # Tentar migrar dados se existirem
                try:
                    cursor.execute("SELECT usuario, perfil, data_cadastro FROM usuarios")
                    usuarios = cursor.fetchall()
                    
                    for user in usuarios:
                        # Criar hash para senha padrão para usuários existentes
                        senha_hash = bcrypt.hashpw(b"sucodepao", bcrypt.gensalt())
                        cursor.execute(
                            "INSERT OR IGNORE INTO usuarios_nova (usuario, senha_hash, perfil, data_cadastro) VALUES (?, ?, ?, ?)",
                            (user[0], senha_hash, user[1], user[2] if len(user) > 2 else None)
                        )
                except:
                    pass  # Se falhar, tabela nova ficará vazia
                
                # Renomear tabelas
                cursor.execute("DROP TABLE IF EXISTS usuarios")
                cursor.execute("ALTER TABLE usuarios_nova RENAME TO usuarios")
        else:
            # Tabela não existe, criar
            cursor.execute("""
                CREATE TABLE usuarios (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    usuario TEXT UNIQUE NOT NULL,
                    senha_hash TEXT NOT NULL,
                    perfil TEXT NOT NULL,
                    data_cadastro TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
    except Exception as e:
        print(f"Erro ao verificar estrutura: {e}")
        # Criar tabela do zero em caso de erro
        cursor.execute("DROP TABLE IF EXISTS usuarios")
        cursor.execute("""
            CREATE TABLE usuarios (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                usuario TEXT UNIQUE NOT NULL,
                senha_hash TEXT NOT NULL,
                perfil TEXT NOT NULL,
                data_cadastro TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
    
    # 3. Verificar se admin existe
    cursor.execute("SELECT COUNT(*) as count FROM usuarios WHERE usuario = 'admin'")
    admin_criado = False
    
    if cursor.fetchone()["count"] == 0:
        # Criar admin com senha "sucodepao"
        senha_hash = bcrypt.hashpw(b"sucodepao", bcrypt.gensalt())
        
        try:
            cursor.execute(
                "INSERT INTO usuarios (usuario, senha_hash, perfil) VALUES (?, ?, ?)",
                ("admin", senha_hash, "admin")
            )
            admin_criado = True
            print("Admin criado com sucesso")
        except Exception as e:
            print(f"Erro ao criar admin: {e}")
            # Tentar método alternativo
            try:
                cursor.execute(
                    "INSERT OR IGNORE INTO usuarios (usuario, senha_hash, perfil) VALUES (?, ?, ?)",
                    ("admin", senha_hash, "admin")
                )
                admin_criado = True
            except:
                admin_criado = False
    
    # 4. Limpar tabelas temporárias
    cursor.execute("DROP TABLE IF EXISTS usuarios_temp")
    cursor.execute("DROP TABLE IF EXISTS usuarios_nova")
    
    conn.commit()
    conn.close()
    
    return admin_criado


def verificar_senha(senha_digitada, senha_hash_armazenada):
    """Verifica se a senha digitada corresponde ao hash armazenado."""
    try:
        if isinstance(senha_hash_armazenada, str):
            senha_hash_armazenada = senha_hash_armazenada.encode('utf-8')
        
        return bcrypt.checkpw(senha_digitada.encode('utf-8'), senha_hash_armazenada)
    except Exception as e:
        print(f"Erro ao verificar senha: {e}")
        return False
