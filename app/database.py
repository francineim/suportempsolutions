import sqlite3
import os

def conectar():
    """Conecta ao banco de dados SQLite."""
    # Garantir que a pasta data existe
    if not os.path.exists("data"):
        os.makedirs("data")
    
    conn = sqlite3.connect("data/database.db", check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn

def criar_tabelas():
    """Cria todas as tabelas necessárias."""
    conn = conectar()
    cursor = conn.cursor()
    
    try:
        # Tabela de usuários COMPLETA
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
        
        # Adicionar colunas novas se não existirem
        try:
            cursor.execute("ALTER TABLE usuarios ADD COLUMN nome_completo TEXT")
        except:
            pass  # Coluna já existe
            
        try:
            cursor.execute("ALTER TABLE usuarios ADD COLUMN empresa TEXT")
        except:
            pass  # Coluna já existe
            
        try:
            cursor.execute("ALTER TABLE usuarios ADD COLUMN email TEXT")
        except:
            pass  # Coluna já existe
            
        try:
            cursor.execute("ALTER TABLE usuarios ADD COLUMN ativo INTEGER DEFAULT 1")
        except:
            pass  # Coluna já existe
        
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
        
        # Verificar se admin existe
        cursor.execute("SELECT COUNT(*) FROM usuarios WHERE usuario = 'admin'")
        if cursor.fetchone()[0] == 0:
            cursor.execute(
                "INSERT INTO usuarios (usuario, senha, perfil, nome_completo, empresa, email) VALUES (?, ?, ?, ?, ?, ?)",
                ("admin", "sucodepao", "admin", "Administrador do Sistema", "MP Solutions", "admin@mpsolutions.com.br")
            )
        
        conn.commit()
        return True
        
    except Exception as e:
        print(f"Erro ao criar tabelas: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()

# ========== FUNÇÕES PARA USUÁRIOS ==========
def cadastrar_usuario_completo(usuario, senha, perfil, nome_completo, empresa, email):
    """Cadastra um usuário com todos os dados."""
    conn = conectar()
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            INSERT INTO usuarios (usuario, senha, perfil, nome_completo, empresa, email)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (usuario, senha, perfil, nome_completo, empresa, email))
        
        conn.commit()
        return True
    except Exception as e:
        conn.rollback()
        print(f"Erro ao cadastrar usuário: {e}")
        return False
    finally:
        conn.close()

def listar_usuarios():
    """Lista todos os usuários cadastrados."""
    conn = conectar()
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            SELECT id, usuario, perfil, nome_completo, empresa, email, 
                   data_cadastro, ativo
            FROM usuarios
            ORDER BY usuario
        """)
        return cursor.fetchall()
    finally:
        conn.close()

def excluir_usuario(usuario_id):
    """Exclui um usuário pelo ID."""
    conn = conectar()
    cursor = conn.cursor()
    
    try:
        # Não permitir excluir o admin
        cursor.execute("SELECT usuario FROM usuarios WHERE id = ?", (usuario_id,))
        user = cursor.fetchone()
        
        if user and user["usuario"] == "admin":
            return False, "Não é possível excluir o usuário administrador"
        
        cursor.execute("DELETE FROM usuarios WHERE id = ?", (usuario_id,))
        conn.commit()
        return True, "Usuário excluído com sucesso"
    except Exception as e:
        conn.rollback()
        return False, f"Erro ao excluir usuário: {e}"
    finally:
        conn.close()

def buscar_usuario_por_id(usuario_id):
    """Busca um usuário pelo ID."""
    conn = conectar()
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            SELECT id, usuario, perfil, nome_completo, empresa, email, ativo
            FROM usuarios WHERE id = ?
        """, (usuario_id,))
        return cursor.fetchone()
    finally:
        conn.close()

def atualizar_usuario(usuario_id, dados):
    """Atualiza os dados de um usuário."""
    conn = conectar()
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            UPDATE usuarios 
            SET nome_completo = ?, empresa = ?, email = ?, perfil = ?
            WHERE id = ?
        """, (dados['nome_completo'], dados['empresa'], dados['email'], 
              dados['perfil'], usuario_id))
        
        conn.commit()
        return True
    except Exception as e:
        conn.rollback()
        print(f"Erro ao atualizar usuário: {e}")
        return False
    finally:
        conn.close()

# ========== FUNÇÕES PARA CHAMADOS ==========
def buscar_chamados(usuario=None, perfil=None):
    """Busca chamados baseado no perfil."""
    conn = conectar()
    cursor = conn.cursor()
    
    try:
        if perfil == "admin":
            cursor.execute("""
                SELECT id, assunto, prioridade, status, data_abertura, usuario, atendente
                FROM chamados
                ORDER BY data_abertura DESC
            """)
        else:
            cursor.execute("""
                SELECT id, assunto, prioridade, status, data_abertura, usuario, atendente
                FROM chamados
                WHERE usuario = ?
                ORDER BY data_abertura DESC
            """, (usuario,))
        
        return cursor.fetchall()
    finally:
        conn.close()

def buscar_descricao_chamado(chamado_id):
    """Busca a descrição completa de um chamado."""
    conn = conectar()
    cursor = conn.cursor()
    
    try:
        cursor.execute("SELECT descricao FROM chamados WHERE id = ?", (chamado_id,))
        resultado = cursor.fetchone()
        return resultado["descricao"] if resultado else ""
    finally:
        conn.close()

def salvar_anexo(chamado_id, nome_arquivo, caminho_arquivo):
    """Salva um anexo no banco de dados."""
    conn = conectar()
    cursor = conn.cursor()
    
    try:
        cursor.execute(
            "INSERT INTO anexos (chamado_id, nome_arquivo, caminho_arquivo) VALUES (?, ?, ?)",
            (chamado_id, nome_arquivo, caminho_arquivo)
        )
        conn.commit()
        return True
    except Exception as e:
        conn.rollback()
        print(f"Erro ao salvar anexo: {e}")
        return False
    finally:
        conn.close()

def buscar_anexos(chamado_id):
    """Busca anexos de um chamado."""
    conn = conectar()
    cursor = conn.cursor()
    
    try:
        cursor.execute(
            "SELECT id, nome_arquivo, data_upload, caminho_arquivo FROM anexos WHERE chamado_id = ? ORDER BY data_upload DESC",
            (chamado_id,)
        )
        return cursor.fetchall()
    finally:
        conn.close()
