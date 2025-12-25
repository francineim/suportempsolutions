# app/database.py - VERSÃO CORRIGIDA
import sqlite3
import os
from datetime import datetime
from utils import hash_senha, formatar_tempo, parse_datetime_safe

def conectar():
    """Conecta ao banco de dados SQLite."""
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
        # Tabela de usuários
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS usuarios (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                usuario TEXT UNIQUE NOT NULL,
                senha_hash TEXT NOT NULL,
                salt TEXT NOT NULL,
                perfil TEXT NOT NULL,
                nome_completo TEXT,
                empresa TEXT,
                email TEXT UNIQUE,
                data_cadastro TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                ativo INTEGER DEFAULT 1
            )
        """)
        
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
                atendente TEXT,
                data_inicio_atendimento TIMESTAMP,
                data_fim_atendimento TIMESTAMP,
                tempo_atendimento_segundos INTEGER DEFAULT 0,
                status_atendimento TEXT DEFAULT 'nao_iniciado',
                ultima_retomada TIMESTAMP
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
        
        # Índices
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_chamados_status ON chamados(status)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_chamados_usuario ON chamados(usuario)")
        
        # Verificar se admin existe
        cursor.execute("SELECT COUNT(*) FROM usuarios WHERE usuario = 'admin'")
        if cursor.fetchone()[0] == 0:
            senha_hash, salt = hash_senha("sucodepao")
            cursor.execute(
                "INSERT INTO usuarios (usuario, senha_hash, salt, perfil, nome_completo, empresa, email) VALUES (?, ?, ?, ?, ?, ?, ?)",
                ("admin", senha_hash, salt, "admin", "Administrador", "MP Solutions", "admin@mp.com")
            )
        
        conn.commit()
        return True
    except Exception as e:
        print(f"Erro ao criar tabelas: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()

# ========== USUÁRIOS ==========

def cadastrar_usuario_completo(usuario, senha, perfil, nome_completo, empresa, email):
    """Cadastra novo usuário."""
    try:
        conn = conectar()
        cursor = conn.cursor()
        
        senha_hash, salt = hash_senha(senha)
        
        cursor.execute("""
            INSERT INTO usuarios 
            (usuario, senha_hash, salt, perfil, nome_completo, empresa, email)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (usuario, senha_hash, salt, perfil, nome_completo, empresa, email))
        
        conn.commit()
        conn.close()
        return True
    except:
        return False

def listar_usuarios():
    """Lista todos os usuários."""
    try:
        conn = conectar()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM usuarios ORDER BY usuario")
        usuarios = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return usuarios
    except:
        return []

def buscar_usuario_por_id(user_id):
    """Busca usuário por ID."""
    try:
        conn = conectar()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM usuarios WHERE id = ?", (user_id,))
        usuario = cursor.fetchone()
        conn.close()
        return dict(usuario) if usuario else None
    except:
        return None

def atualizar_usuario(user_id, dados):
    """Atualiza dados de usuário."""
    try:
        conn = conectar()
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE usuarios
            SET nome_completo = ?, empresa = ?, email = ?, perfil = ?
            WHERE id = ?
        """, (dados['nome_completo'], dados['empresa'], dados['email'], dados['perfil'], user_id))
        conn.commit()
        conn.close()
        return True
    except:
        return False

def excluir_usuario(user_id):
    """Desativa usuário."""
    try:
        conn = conectar()
        cursor = conn.cursor()
        cursor.execute("UPDATE usuarios SET ativo = 0 WHERE id = ?", (user_id,))
        conn.commit()
        conn.close()
        return True
    except:
        return False

# ========== CHAMADOS ==========

def buscar_chamados(usuario, perfil):
    """Busca chamados baseado no perfil."""
    try:
        conn = conectar()
        cursor = conn.cursor()
        
        if perfil == "admin":
            cursor.execute("SELECT * FROM chamados ORDER BY id DESC")
        else:
            cursor.execute("SELECT * FROM chamados WHERE usuario = ? ORDER BY id DESC", (usuario,))
        
        chamados = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return chamados
    except Exception as e:
        print(f"Erro buscar chamados: {e}")
        return []

def buscar_descricao_chamado(chamado_id):
    """Busca descrição de um chamado."""
    try:
        conn = conectar()
        cursor = conn.cursor()
        cursor.execute("SELECT descricao FROM chamados WHERE id = ?", (chamado_id,))
        resultado = cursor.fetchone()
        conn.close()
        return resultado['descricao'] if resultado else ""
    except:
        return ""

# ========== ATENDIMENTO ==========

def iniciar_atendimento_admin(chamado_id, atendente):
    """Admin inicia atendimento."""
    try:
        conn = conectar()
        cursor = conn.cursor()
        
        agora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        cursor.execute("""
            UPDATE chamados
            SET status = 'Em atendimento',
                atendente = ?,
                data_inicio_atendimento = ?,
                status_atendimento = 'em_andamento',
                ultima_retomada = ?,
                tempo_atendimento_segundos = 0
            WHERE id = ? AND status = 'Novo'
        """, (atendente, agora, agora, chamado_id))
        
        if cursor.rowcount > 0:
            conn.commit()
            conn.close()
            return True, "✅ Atendimento iniciado!"
        else:
            conn.close()
            return False, "❌ Erro ao iniciar"
    except Exception as e:
        return False, f"Erro: {e}"

def pausar_atendimento(chamado_id):
    """Pausa o cronômetro."""
    try:
        conn = conectar()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT tempo_atendimento_segundos, ultima_retomada
            FROM chamados
            WHERE id = ? AND status_atendimento = 'em_andamento'
        """, (chamado_id,))
        
        dados = cursor.fetchone()
        
        if not dados:
            conn.close()
            return False, "Não está em andamento"
        
        tempo_atual = dados['tempo_atendimento_segundos'] or 0
        
        if dados['ultima_retomada']:
            ultima_retomada = parse_datetime_safe(dados['ultima_retomada'])
            if ultima_retomada:
                tempo_decorrido = int((datetime.now() - ultima_retomada).total_seconds())
                tempo_atual += tempo_decorrido
        
        cursor.execute("""
            UPDATE chamados
            SET status_atendimento = 'pausado',
                tempo_atendimento_segundos = ?,
                ultima_retomada = NULL
            WHERE id = ?
        """, (tempo_atual, chamado_id))
        
        conn.commit()
        conn.close()
        return True, f"⏸️ Pausado. Tempo: {formatar_tempo(tempo_atual)}"
    except Exception as e:
        return False, f"Erro: {e}"

def retomar_atendimento(chamado_id):
    """Retoma o cronômetro."""
    try:
        conn = conectar()
        cursor = conn.cursor()
        
        agora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        cursor.execute("""
            UPDATE chamados
            SET status_atendimento = 'em_andamento',
                ultima_retomada = ?
            WHERE id = ? AND status_atendimento = 'pausado'
        """, (agora, chamado_id))
        
        if cursor.rowcount > 0:
            conn.commit()
            conn.close()
            return True, "▶️ Retomado!"
        else:
            conn.close()
            return False, "Não está pausado"
    except Exception as e:
        return False, f"Erro: {e}"

def concluir_atendimento_admin(chamado_id):
    """Admin conclui o atendimento."""
    try:
        conn = conectar()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT tempo_atendimento_segundos, ultima_retomada, status_atendimento
            FROM chamados
            WHERE id = ? AND status = 'Em atendimento'
        """, (chamado_id,))
        
        dados = cursor.fetchone()
        
        if not dados:
            conn.close()
            return False, "Não está em atendimento"
        
        tempo_final = dados['tempo_atendimento_segundos'] or 0
        
        if dados['status_atendimento'] == 'em_andamento' and dados['ultima_retomada']:
            ultima_retomada = parse_datetime_safe(dados['ultima_retomada'])
            if ultima_retomada:
                tempo_decorrido = int((datetime.now() - ultima_retomada).total_seconds())
                tempo_final += tempo_decorrido
        
        agora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        cursor.execute("""
            UPDATE chamados
            SET status = 'Concluído',
                data_fim_atendimento = ?,
                tempo_atendimento_segundos = ?,
                status_atendimento = 'concluido'
            WHERE id = ?
        """, (agora, tempo_final, chamado_id))
        
        conn.commit()
        conn.close()
        
        return True, f"✅ Concluído! Tempo: {formatar_tempo(tempo_final)}"
    except Exception as e:
        return False, f"Erro: {e}"

def cliente_concluir_chamado(chamado_id, usuario):
    """Cliente marca como concluído."""
    try:
        conn = conectar()
        cursor = conn.cursor()
        
        agora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        cursor.execute("""
            UPDATE chamados
            SET status = 'Concluído',
                data_fim_atendimento = ?
            WHERE id = ? AND usuario = ?
        """, (agora, chamado_id, usuario))
        
        if cursor.rowcount > 0:
            conn.commit()
            conn.close()
            return True, "✅ Marcado como concluído!"
        else:
            conn.close()
            return False, "Erro"
    except Exception as e:
        return False, f"Erro: {e}"

def obter_tempo_atendimento(chamado_id):
    """Obtém tempo atual de atendimento."""
    try:
        conn = conectar()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT tempo_atendimento_segundos, ultima_retomada, status_atendimento
            FROM chamados
            WHERE id = ?
        """, (chamado_id,))
        
        dados = cursor.fetchone()
        conn.close()
        
        if not dados:
            return 0
        
        tempo_atual = dados['tempo_atendimento_segundos'] or 0
        
        if dados['status_atendimento'] == 'em_andamento' and dados['ultima_retomada']:
            ultima_retomada = parse_datetime_safe(dados['ultima_retomada'])
            if ultima_retomada:
                tempo_decorrido = int((datetime.now() - ultima_retomada).total_seconds())
                tempo_atual += tempo_decorrido
        
        return tempo_atual
    except:
        return 0

# ========== ANEXOS ==========

def salvar_anexo(chamado_id, nome_arquivo, caminho_arquivo):
    """Salva anexo no banco."""
    try:
        conn = conectar()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO anexos (chamado_id, nome_arquivo, caminho_arquivo)
            VALUES (?, ?, ?)
        """, (chamado_id, nome_arquivo, caminho_arquivo))
        conn.commit()
        conn.close()
        return True
    except:
        return False

def buscar_anexos(chamado_id):
    """Busca anexos de um chamado."""
    try:
        conn = conectar()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM anexos WHERE chamado_id = ?", (chamado_id,))
        anexos = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return anexos
    except:
        return []

def excluir_anexo(anexo_id):
    """Exclui um anexo."""
    try:
        conn = conectar()
        cursor = conn.cursor()
        cursor.execute("SELECT caminho_arquivo FROM anexos WHERE id = ?", (anexo_id,))
        resultado = cursor.fetchone()
        
        if resultado and os.path.exists(resultado['caminho_arquivo']):
            os.remove(resultado['caminho_arquivo'])
        
        cursor.execute("DELETE FROM anexos WHERE id = ?", (anexo_id,))
        conn.commit()
        conn.close()
        return True
    except:
        return False

# ========== ESTATÍSTICAS ==========

def buscar_estatisticas_usuario(usuario, perfil):
    """Busca estatísticas."""
    try:
        conn = conectar()
        cursor = conn.cursor()
        
        if perfil == "admin":
            cursor.execute("SELECT COUNT(*) as total FROM chamados")
            total = cursor.fetchone()['total']
            cursor.execute("SELECT COUNT(*) as novos FROM chamados WHERE status = 'Novo'")
            novos = cursor.fetchone()['novos']
            cursor.execute("SELECT COUNT(*) as em_atendimento FROM chamados WHERE status = 'Em atendimento'")
            em_atendimento = cursor.fetchone()['em_atendimento']
            cursor.execute("SELECT COUNT(*) as concluidos FROM chamados WHERE status = 'Concluído'")
            concluidos = cursor.fetchone()['concluidos']
        else:
            cursor.execute("SELECT COUNT(*) as total FROM chamados WHERE usuario = ?", (usuario,))
            total = cursor.fetchone()['total']
            cursor.execute("SELECT COUNT(*) as novos FROM chamados WHERE usuario = ? AND status = 'Novo'", (usuario,))
            novos = cursor.fetchone()['novos']
            cursor.execute("SELECT COUNT(*) as em_atendimento FROM chamados WHERE usuario = ? AND status = 'Em atendimento'", (usuario,))
            em_atendimento = cursor.fetchone()['em_atendimento']
            cursor.execute("SELECT COUNT(*) as concluidos FROM chamados WHERE usuario = ? AND status = 'Concluído'", (usuario,))
            concluidos = cursor.fetchone()['concluidos']
        
        conn.close()
        
        return {
            "total": total,
            "novos": novos,
            "em_atendimento": em_atendimento,
            "concluidos": concluidos
        }
    except:
        return {"total": 0, "novos": 0, "em_atendimento": 0, "concluidos": 0}
