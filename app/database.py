import sqlite3
import os
from datetime import datetime

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
        
        # Tabela de chamados COM CAMPOS DE TEMPO DE ATENDIMENTO
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
                atendente TEXT,
                -- Campos para controle de tempo de atendimento
                status_atendimento TEXT DEFAULT 'nao_iniciado', -- nao_iniciado, em_andamento, pausado, concluido
                ultima_retomada TIMESTAMP,
                tempo_total_atendimento INTEGER DEFAULT 0 -- em segundos
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
        
        # Tabela para registrar pausas e retomadas (histórico)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS historico_atendimento (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                chamado_id INTEGER NOT NULL,
                acao TEXT NOT NULL, -- inicio, pausa, retomada, conclusao
                data_hora TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                observacao TEXT,
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
        print("✅ Tabelas criadas/verificadas com sucesso!")
        return True
        
    except Exception as e:
        print(f"❌ Erro ao criar tabelas: {e}")
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

# ========== FUNÇÕES PARA CHAMADOS ==========
def buscar_chamados(usuario=None, perfil=None):
    """Busca chamados baseado no perfil."""
    conn = conectar()
    cursor = conn.cursor()
    
    try:
        if perfil == "admin":
            cursor.execute("""
                SELECT id, assunto, prioridade, status, data_abertura, usuario, atendente,
                       status_atendimento, tempo_total_atendimento
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
                SELECT id, assunto, prioridade, status, data_abertura, usuario, atendente,
                       status_atendimento, tempo_total_atendimento
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

def iniciar_atendimento(chamado_id, atendente):
    """Inicia o atendimento de um chamado."""
    conn = conectar()
    cursor = conn.cursor()
    
    try:
        # Atualizar status do chamado
        cursor.execute("""
            UPDATE chamados 
            SET status = 'Em atendimento',
                atendente = ?,
                data_atendimento = CURRENT_TIMESTAMP,
                status_atendimento = 'em_andamento',
                ultima_retomada = CURRENT_TIMESTAMP
            WHERE id = ?
        """, (atendente, chamado_id))
        
        # Registrar no histórico
        cursor.execute("""
            INSERT INTO historico_atendimento (chamado_id, acao)
            VALUES (?, 'inicio')
        """, (chamado_id,))
        
        conn.commit()
        return True
    except Exception as e:
        conn.rollback()
        print(f"Erro ao iniciar atendimento: {e}")
        return False
    finally:
        conn.close()

def pausar_atendimento(chamado_id):
    """Pausa o atendimento de um chamado."""
    conn = conectar()
    cursor = conn.cursor()
    
    try:
        # Calcular tempo decorrido desde a última retomada
        cursor.execute("""
            SELECT ultima_retomada FROM chamados WHERE id = ?
        """, (chamado_id,))
        
        resultado = cursor.fetchone()
        if resultado and resultado["ultima_retomada"]:
            # Calcular diferença em segundos
            cursor.execute("""
                SELECT (julianday('now') - julianday(?)) * 86400 as segundos
            """, (resultado["ultima_retomada"],))
            
            segundos = cursor.fetchone()["segundos"]
            
            # Atualizar tempo total
            cursor.execute("""
                UPDATE chamados 
                SET tempo_total_atendimento = tempo_total_atendimento + ?,
                    status_atendimento = 'pausado',
                    ultima_retomada = NULL
                WHERE id = ?
            """, (int(segundos), chamado_id))
        
        # Registrar no histórico
        cursor.execute("""
            INSERT INTO historico_atendimento (chamado_id, acao)
            VALUES (?, 'pausa')
        """, (chamado_id,))
        
        conn.commit()
        return True
    except Exception as e:
        conn.rollback()
        print(f"Erro ao pausar atendimento: {e}")
        return False
    finally:
        conn.close()

def retomar_atendimento(chamado_id):
    """Retoma o atendimento de um chamado."""
    conn = conectar()
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            UPDATE chamados 
            SET status_atendimento = 'em_andamento',
                ultima_retomada = CURRENT_TIMESTAMP
            WHERE id = ?
        """, (chamado_id,))
        
        # Registrar no histórico
        cursor.execute("""
            INSERT INTO historico_atendimento (chamado_id, acao)
            VALUES (?, 'retomada')
        """, (chamado_id,))
        
        conn.commit()
        return True
    except Exception as e:
        conn.rollback()
        print(f"Erro ao retomar atendimento: {e}")
        return False
    finally:
        conn.close()

def concluir_atendimento_admin(chamado_id):
    """Conclui o atendimento pelo admin."""
    conn = conectar()
    cursor = conn.cursor()
    
    try:
        # Se estiver em andamento, calcular tempo até agora
        cursor.execute("""
            SELECT status_atendimento, ultima_retomada FROM chamados WHERE id = ?
        """, (chamado_id,))
        
        resultado = cursor.fetchone()
        if resultado and resultado["status_atendimento"] == 'em_andamento' and resultado["ultima_retomada"]:
            # Calcular diferença em segundos
            cursor.execute("""
                SELECT (julianday('now') - julianday(?)) * 86400 as segundos
            """, (resultado["ultima_retomada"],))
            
            segundos = cursor.fetchone()["segundos"]
            
            # Atualizar tempo total
            cursor.execute("""
                UPDATE chamados 
                SET tempo_total_atendimento = tempo_total_atendimento + ?
                WHERE id = ?
            """, (int(segundos), chamado_id))
        
        # Atualizar status do chamado
        cursor.execute("""
            UPDATE chamados 
            SET status = 'Concluído',
                data_fechamento = CURRENT_TIMESTAMP,
                status_atendimento = 'concluido',
                ultima_retomada = NULL
            WHERE id = ?
        """, (chamado_id,))
        
        # Registrar no histórico
        cursor.execute("""
            INSERT INTO historico_atendimento (chamado_id, acao)
            VALUES (?, 'conclusao_admin')
        """, (chamado_id,))
        
        conn.commit()
        return True
    except Exception as e:
        conn.rollback()
        print(f"Erro ao concluir atendimento: {e}")
        return False
    finally:
        conn.close()

def cliente_concluir_chamado(chamado_id):
    """Conclui o chamado pelo cliente."""
    conn = conectar()
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            UPDATE chamados 
            SET status = 'Concluído',
                data_fechamento = CURRENT_TIMESTAMP,
                status_atendimento = 'concluido',
                ultima_retomada = NULL
            WHERE id = ?
        """, (chamado_id,))
        
        # Registrar no histórico
        cursor.execute("""
            INSERT INTO historico_atendimento (chamado_id, acao)
            VALUES (?, 'conclusao_cliente')
        """, (chamado_id,))
        
        conn.commit()
        return True
    except Exception as e:
        conn.rollback()
        print(f"Erro ao concluir chamado: {e}")
        return False
    finally:
        conn.close()

def calcular_tempo_atendimento(chamado_id):
    """Calcula o tempo total de atendimento de um chamado."""
    conn = conectar()
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            SELECT 
                tempo_total_atendimento,
                status_atendimento,
                ultima_retomada
            FROM chamados WHERE id = ?
        """, (chamado_id,))
        
        resultado = cursor.fetchone()
        if not resultado:
            return 0
        
        tempo_total = resultado["tempo_total_atendimento"] or 0
        
        # Se estiver em andamento, adicionar tempo desde a última retomada
        if resultado["status_atendimento"] == 'em_andamento' and resultado["ultima_retomada"]:
            cursor.execute("""
                SELECT (julianday('now') - julianday(?)) * 86400 as segundos
            """, (resultado["ultima_retomada"],))
            
            segundos = cursor.fetchone()["segundos"]
            tempo_total += int(segundos)
        
        return tempo_total
    finally:
        conn.close()

def formatar_tempo(segundos):
    """Formata segundos em uma string legível."""
    if segundos < 60:
        return f"{segundos} segundos"
    elif segundos < 3600:
        minutos = segundos // 60
        segundos_resto = segundos % 60
        return f"{minutos} minutos e {segundos_resto} segundos"
    else:
        horas = segundos // 3600
        minutos = (segundos % 3600) // 60
        segundos_resto = segundos % 60
        return f"{horas} horas, {minutos} minutos e {segundos_resto} segundos"

def obter_tempo_atendimento(chamado_id):
    """Obtém e formata o tempo de atendimento."""
    segundos = calcular_tempo_atendimento(chamado_id)
    return formatar_tempo(segundos)

# ========== FUNÇÕES PARA ANEXOS ==========
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
