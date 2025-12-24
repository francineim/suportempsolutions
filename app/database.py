import sqlite3
import os

def conectar():
    """Conecta ao banco de dados SQLite."""
    conn = sqlite3.connect("data/database.db", check_same_thread=False)  # Agora em data/
    conn.row_factory = sqlite3.Row
    return conn


def criar_tabelas():
    """Cria todas as tabelas necessárias."""
    # Garantir que a pasta data existe
    if not os.path.exists("data"):
        os.makedirs("data")
    
    # Garantir que a pasta uploads existe
    if not os.path.exists("uploads"):
        os.makedirs("uploads")
    
    conn = conectar()
    cursor = conn.cursor()
    
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
    
    # Tabela de chamados (com campos adicionais)
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
    
    # NOVA: Tabela de anexos
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
            "INSERT INTO usuarios (usuario, senha, perfil) VALUES (?, ?, ?)",
            ("admin", "sucodepao", "admin")
        )
    
    conn.commit()
    conn.close()
    return True


# ========== FUNÇÕES PARA ANEXOS ==========
def salvar_anexo(chamado_id, nome_arquivo, caminho_arquivo):
    """Salva um anexo no banco de dados."""
    conn = conectar()
    cursor = conn.cursor()
    
    cursor.execute(
        "INSERT INTO anexos (chamado_id, nome_arquivo, caminho_arquivo) VALUES (?, ?, ?)",
        (chamado_id, nome_arquivo, caminho_arquivo)
    )
    
    conn.commit()
    conn.close()
    return True


def buscar_anexos(chamado_id):
    """Busca anexos de um chamado."""
    conn = conectar()
    cursor = conn.cursor()
    
    cursor.execute(
        "SELECT id, nome_arquivo, data_upload, caminho_arquivo FROM anexos WHERE chamado_id = ? ORDER BY data_upload DESC",
        (chamado_id,)
    )
    
    anexos = cursor.fetchall()
    conn.close()
    return anexos


def excluir_anexo(anexo_id):
    """Exclui um anexo específico."""
    conn = conectar()
    cursor = conn.cursor()
    
    # Buscar caminho do arquivo
    cursor.execute("SELECT caminho_arquivo FROM anexos WHERE id = ?", (anexo_id,))
    resultado = cursor.fetchone()
    
    if resultado:
        caminho = resultado["caminho_arquivo"]
        # Excluir arquivo físico
        if os.path.exists(caminho):
            os.remove(caminho)
    
    # Excluir do banco
    cursor.execute("DELETE FROM anexos WHERE id = ?", (anexo_id,))
    
    conn.commit()
    conn.close()
    return True


# ========== FUNÇÕES PARA CHAMADOS ==========
def buscar_chamados(usuario=None, perfil=None):
    """Busca chamados baseado no perfil."""
    conn = conectar()
    cursor = conn.cursor()
    
    if perfil == "admin":
        cursor.execute("""
            SELECT id, assunto, prioridade, status, data_abertura, usuario, atendente
            FROM chamados
            ORDER BY 
                CASE status 
                    WHEN 'Novo' THEN 1
                    WHEN 'Em atendimento' THEN 2
                    WHEN 'Concluído' THEN 3
                END,
                data_abertura DESC
        """)
    else:
        cursor.execute("""
            SELECT id, assunto, prioridade, status, data_abertura, usuario, atendente
            FROM chamados
            WHERE usuario = ?
            ORDER BY 
                CASE status 
                    WHEN 'Novo' THEN 1
                    WHEN 'Em atendimento' THEN 2
                    WHEN 'Concluído' THEN 3
                END,
                data_abertura DESC
        """, (usuario,))
    
    chamados = cursor.fetchall()
    conn.close()
    return chamados


def excluir_chamado(chamado_id):
    """Exclui um chamado e seus anexos."""
    conn = conectar()
    cursor = conn.cursor()
    
    # Buscar caminhos dos anexos para excluir arquivos
    cursor.execute("SELECT caminho_arquivo FROM anexos WHERE chamado_id = ?", (chamado_id,))
    anexos = cursor.fetchall()
    
    # Excluir arquivos físicos
    for anexo in anexos:
        caminho = anexo["caminho_arquivo"]
        if os.path.exists(caminho):
            os.remove(caminho)
    
    # Excluir do banco (CASCADE excluirá os anexos automaticamente)
    cursor.execute("DELETE FROM chamados WHERE id = ?", (chamado_id,))
    
    conn.commit()
    conn.close()
    return True


def atualizar_status_chamado(chamado_id, novo_status, atendente=None):
    """Atualiza o status de um chamado."""
    conn = conectar()
    cursor = conn.cursor()
    
    if novo_status == "Em atendimento":
        cursor.execute("""
            UPDATE chamados 
            SET status = ?, atendente = ?, data_atendimento = CURRENT_TIMESTAMP 
            WHERE id = ?
        """, (novo_status, atendente, chamado_id))
    elif novo_status == "Concluído":
        cursor.execute("""
            UPDATE chamados 
            SET status = ?, data_fechamento = CURRENT_TIMESTAMP 
            WHERE id = ?
        """, (novo_status, chamado_id))
    else:
        cursor.execute("""
            UPDATE chamados SET status = ? WHERE id = ?
        """, (novo_status, chamado_id))
    
    conn.commit()
    conn.close()
    return True


def buscar_descricao_chamado(chamado_id):
    """Busca a descrição completa de um chamado."""
    conn = conectar()
    cursor = conn.cursor()
    
    cursor.execute("SELECT descricao FROM chamados WHERE id = ?", (chamado_id,))
    resultado = cursor.fetchone()
    
    conn.close()
    return resultado["descricao"] if resultado else ""
