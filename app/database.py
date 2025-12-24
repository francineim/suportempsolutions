import sqlite3
import os
from datetime import datetime, timedelta

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
                senha TEXT NOT NULL,
                perfil TEXT NOT NULL,
                nome_completo TEXT,
                empresa TEXT,
                email TEXT UNIQUE,
                data_cadastro TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                ativo INTEGER DEFAULT 1
            )
        """)
        
        # Tabela de chamados COM CONTROLE DE TEMPO
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS chamados (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                assunto TEXT NOT NULL,
                prioridade TEXT NOT NULL,
                descricao TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'Novo',
                usuario TEXT NOT NULL,
                data_abertura TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                data_inicio_atendimento TIMESTAMP,
                data_fim_atendimento TIMESTAMP,
                atendente TEXT,
                tempo_atendimento_segundos INTEGER DEFAULT 0,  -- Tempo acumulado em segundos
                status_atendimento TEXT DEFAULT 'nao_iniciado', -- 'nao_iniciado', 'em_andamento', 'pausado', 'concluido'
                ultima_retomada TIMESTAMP,
                tempo_pausado_segundos INTEGER DEFAULT 0
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
        
        # Tabela de histórico de atendimento
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS historico_atendimento (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                chamado_id INTEGER NOT NULL,
                acao TEXT NOT NULL,  -- 'iniciado', 'pausado', 'retomado', 'concluido'
                data_hora TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                tempo_acumulado_segundos INTEGER,
                atendente TEXT,
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

# ========== FUNÇÕES PARA DASHBOARD (ITEM 1) ==========
def buscar_estatisticas_usuario(usuario=None, perfil=None):
    """Busca estatísticas baseadas no perfil."""
    conn = conectar()
    cursor = conn.cursor()
    
    try:
        if perfil == "admin":
            # Admin vê todos
            cursor.execute("SELECT COUNT(*) FROM chamados")
            total = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM chamados WHERE status = 'Novo'")
            novos = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM chamados WHERE status = 'Em atendimento'")
            atendimento = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM chamados WHERE status = 'Concluído'")
            concluidos = cursor.fetchone()[0]
        else:
            # Usuário vê apenas os seus
            cursor.execute("SELECT COUNT(*) FROM chamados WHERE usuario = ?", (usuario,))
            total = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM chamados WHERE usuario = ? AND status = 'Novo'", (usuario,))
            novos = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM chamados WHERE usuario = ? AND status = 'Em atendimento'", (usuario,))
            atendimento = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM chamados WHERE usuario = ? AND status = 'Concluído'", (usuario,))
            concluidos = cursor.fetchone()[0]
        
        return {
            "total": total,
            "novos": novos,
            "em_atendimento": atendimento,
            "concluidos": concluidos
        }
    finally:
        conn.close()

# ========== FUNÇÕES PARA CONTROLE DE ATENDIMENTO ==========
def iniciar_atendimento_admin(chamado_id, atendente):
    """ITEM 2: Admin inicia atendimento."""
    conn = conectar()
    cursor = conn.cursor()
    
    try:
        # Verificar se chamado existe e está como 'Novo'
        cursor.execute("SELECT status FROM chamados WHERE id = ?", (chamado_id,))
        chamado = cursor.fetchone()
        
        if not chamado or chamado["status"] != "Novo":
            return False, "Chamado não encontrado ou não está como 'Novo'"
        
        # Atualizar status e iniciar cronômetro
        cursor.execute("""
            UPDATE chamados 
            SET status = 'Em atendimento',
                atendente = ?,
                data_inicio_atendimento = CURRENT_TIMESTAMP,
                status_atendimento = 'em_andamento',
                ultima_retomada = CURRENT_TIMESTAMP
            WHERE id = ?
        """, (atendente, chamado_id))
        
        # Registrar no histórico
        cursor.execute("""
            INSERT INTO historico_atendimento (chamado_id, acao, atendente, tempo_acumulado_segundos)
            VALUES (?, 'iniciado', ?, 0)
        """, (chamado_id, atendente))
        
        conn.commit()
        return True, "Atendimento iniciado com sucesso"
    except Exception as e:
        conn.rollback()
        return False, f"Erro: {str(e)}"
    finally:
        conn.close()

def pausar_atendimento(chamado_id):
    """ITEM 4: Pausar atendimento."""
    conn = conectar()
    cursor = conn.cursor()
    
    try:
        # Verificar se está em andamento
        cursor.execute("""
            SELECT status, status_atendimento, ultima_retomada, tempo_atendimento_segundos 
            FROM chamados WHERE id = ?
        """, (chamado_id,))
        
        chamado = cursor.fetchone()
        if not chamado or chamado["status_atendimento"] != "em_andamento":
            return False, "Chamado não está em andamento"
        
        # Calcular tempo desde última retomada
        if chamado["ultima_retomada"]:
            tempo_decorrido = int((datetime.now() - datetime.strptime(chamado["ultima_retomada"], "%Y-%m-%d %H:%M:%S")).total_seconds())
            novo_tempo = chamado["tempo_atendimento_segundos"] + tempo_decorrido
            
            # Atualizar tempo e pausar
            cursor.execute("""
                UPDATE chamados 
                SET tempo_atendimento_segundos = ?,
                    status_atendimento = 'pausado',
                    tempo_pausado_segundos = tempo_pausado_segundos + ?
                WHERE id = ?
            """, (novo_tempo, tempo_decorrido, chamado_id))
            
            # Registrar no histórico
            cursor.execute("""
                INSERT INTO historico_atendimento (chamado_id, acao, tempo_acumulado_segundos)
                VALUES (?, 'pausado', ?)
            """, (chamado_id, novo_tempo))
            
            conn.commit()
            return True, "Atendimento pausado"
        
        return False, "Erro ao calcular tempo"
    except Exception as e:
        conn.rollback()
        return False, f"Erro: {str(e)}"
    finally:
        conn.close()

def retomar_atendimento(chamado_id):
    """ITEM 4: Retomar atendimento após pausa."""
    conn = conectar()
    cursor = conn.cursor()
    
    try:
        # Verificar se está pausado
        cursor.execute("SELECT status_atendimento FROM chamados WHERE id = ?", (chamado_id,))
        chamado = cursor.fetchone()
        
        if not chamado or chamado["status_atendimento"] != "pausado":
            return False, "Chamado não está pausado"
        
        # Retomar
        cursor.execute("""
            UPDATE chamados 
            SET status_atendimento = 'em_andamento',
                ultima_retomada = CURRENT_TIMESTAMP
            WHERE id = ?
        """, (chamado_id,))
        
        # Registrar no histórico
        cursor.execute("""
            INSERT INTO historico_atendimento (chamado_id, acao)
            VALUES (?, 'retomado')
        """, (chamado_id,))
        
        conn.commit()
        return True, "Atendimento retomado"
    except Exception as e:
        conn.rollback()
        return False, f"Erro: {str(e)}"
    finally:
        conn.close()

def concluir_atendimento_admin(chamado_id):
    """ITEM 4: Admin conclui atendimento."""
    conn = conectar()
    cursor = conn.cursor()
    
    try:
        # Buscar dados do chamado
        cursor.execute("""
            SELECT status_atendimento, ultima_retomada, tempo_atendimento_segundos 
            FROM chamados WHERE id = ?
        """, (chamado_id,))
        
        chamado = cursor.fetchone()
        if not chamado:
            return False, "Chamado não encontrado"
        
        tempo_final = chamado["tempo_atendimento_segundos"]
        
        # Se estava em andamento, calcular tempo desde última retomada
        if chamado["status_atendimento"] == "em_andamento" and chamado["ultima_retomada"]:
            tempo_decorrido = int((datetime.now() - datetime.strptime(chamado["ultima_retomada"], "%Y-%m-%d %H:%M:%S")).total_seconds())
            tempo_final += tempo_decorrido
        
        # Atualizar status e tempo final
        cursor.execute("""
            UPDATE chamados 
            SET status = 'Concluído',
                status_atendimento = 'concluido',
                data_fim_atendimento = CURRENT_TIMESTAMP,
                tempo_atendimento_segundos = ?
            WHERE id = ?
        """, (tempo_final, chamado_id))
        
        # Registrar no histórico
        cursor.execute("""
            INSERT INTO historico_atendimento (chamado_id, acao, tempo_acumulado_segundos)
            VALUES (?, 'concluido_admin', ?)
        """, (chamado_id, tempo_final))
        
        conn.commit()
        return True, f"Atendimento concluído. Tempo total: {formatar_tempo(tempo_final)}"
    except Exception as e:
        conn.rollback()
        return False, f"Erro: {str(e)}"
    finally:
        conn.close()

def cliente_concluir_chamado(chamado_id, usuario):
    """ITEM 3: Cliente conclui seu chamado."""
    conn = conectar()
    cursor = conn.cursor()
    
    try:
        # Verificar se chamado pertence ao usuário e está em atendimento
        cursor.execute("SELECT usuario, status FROM chamados WHERE id = ?", (chamado_id,))
        chamado = cursor.fetchone()
        
        if not chamado:
            return False, "Chamado não encontrado"
        
        if chamado["usuario"] != usuario:
            return False, "Este chamado não pertence a você"
        
        if chamado["status"] != "Em atendimento":
            return False, "Só é possível concluir chamados em atendimento"
        
        # Calcular tempo total se houver
        cursor.execute("""
            SELECT tempo_atendimento_segundos, ultima_retomada, status_atendimento 
            FROM chamados WHERE id = ?
        """, (chamado_id,))
        
        dados = cursor.fetchone()
        tempo_final = dados["tempo_atendimento_segundos"] if dados["tempo_atendimento_segundos"] else 0
        
        # Se estava em andamento, adicionar tempo desde última retomada
        if dados["status_atendimento"] == "em_andamento" and dados["ultima_retomada"]:
            tempo_decorrido = int((datetime.now() - datetime.strptime(dados["ultima_retomada"], "%Y-%m-%d %H:%M:%S")).total_seconds())
            tempo_final += tempo_decorrido
        
        # Atualizar status
        cursor.execute("""
            UPDATE chamados 
            SET status = 'Concluído',
                status_atendimento = 'concluido',
                data_fim_atendimento = CURRENT_TIMESTAMP,
                tempo_atendimento_segundos = ?
            WHERE id = ?
        """, (tempo_final, chamado_id))
        
        # Registrar no histórico
        cursor.execute("""
            INSERT INTO historico_atendimento (chamado_id, acao, tempo_acumulado_segundos)
            VALUES (?, 'concluido_cliente', ?)
        """, (chamado_id, tempo_final))
        
        conn.commit()
        return True, f"Chamado concluído! Tempo de atendimento: {formatar_tempo(tempo_final)}"
    except Exception as e:
        conn.rollback()
        return False, f"Erro: {str(e)}"
    finally:
        conn.close()

def obter_tempo_atendimento(chamado_id):
    """Obtém tempo atual de atendimento."""
    conn = conectar()
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            SELECT tempo_atendimento_segundos, ultima_retomada, status_atendimento 
            FROM chamados WHERE id = ?
        """, (chamado_id,))
        
        dados = cursor.fetchone()
        if not dados:
            return 0
        
        tempo_total = dados["tempo_atendimento_segundos"] or 0
        
        # Se está em andamento, adicionar tempo desde última retomada
        if dados["status_atendimento"] == "em_andamento" and dados["ultima_retomada"]:
            tempo_decorrido = int((datetime.now() - datetime.strptime(dados["ultima_retomada"], "%Y-%m-%d %H:%M:%S")).total_seconds())
            tempo_total += tempo_decorrido
        
        return tempo_total
    finally:
        conn.close()

def formatar_tempo(segundos):
    """Formata segundos para horas:minutos:segundos."""
    if not segundos:
        return "00:00:00"
    
    horas = segundos // 3600
    minutos = (segundos % 3600) // 60
    segundos = segundos % 60
    
    return f"{horas:02d}:{minutos:02d}:{segundos:02d}"

# ========== OUTRAS FUNÇÕES ==========
def buscar_chamados(usuario=None, perfil=None):
    """Busca chamados baseado no perfil."""
    conn = conectar()
    cursor = conn.cursor()
    
    try:
        if perfil == "admin":
            cursor.execute("""
                SELECT id, assunto, prioridade, status, data_abertura, usuario, atendente,
                       tempo_atendimento_segundos, status_atendimento
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
                       tempo_atendimento_segundos, status_atendimento
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
