# app/database.py
import sqlite3
import os
from datetime import datetime
from utils import hash_senha, formatar_tempo

def conectar():
    """Conecta ao banco de dados SQLite."""
    if not os.path.exists("data"):
        os.makedirs("data")
    
    conn = sqlite3.connect("data/database.db", check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def criar_tabelas():
    """Cria todas as tabelas necessárias com migração segura."""
    conn = conectar()
    cursor = conn.cursor()
    
    try:
        # Tabela de usuários COM HASH
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
        
        # Tabela de histórico de atendimento
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS historico_atendimento (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                chamado_id INTEGER NOT NULL,
                acao TEXT NOT NULL,
                data_hora TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                tempo_acumulado_segundos INTEGER,
                atendente TEXT,
                FOREIGN KEY (chamado_id) REFERENCES chamados(id) ON DELETE CASCADE
            )
        """)
        
        # Tabela de logs de auditoria
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS logs_auditoria (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                acao TEXT NOT NULL,
                usuario TEXT NOT NULL,
                detalhes TEXT,
                data_hora TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Criar índices para performance
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_chamados_status ON chamados(status)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_chamados_usuario ON chamados(usuario)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_anexos_chamado ON anexos(chamado_id)")
        
        # Verificar se admin existe (COM HASH AGORA)
        cursor.execute("SELECT COUNT(*) FROM usuarios WHERE usuario = 'admin'")
        if cursor.fetchone()[0] == 0:
            senha_hash, salt = hash_senha("sucodepao")
            cursor.execute(
                "INSERT INTO usuarios (usuario, senha_hash, salt, perfil, nome_completo, empresa, email) VALUES (?, ?, ?, ?, ?, ?, ?)",
                ("admin", senha_hash, salt, "admin", "Administrador do Sistema", "MP Solutions", "admin@mpsolutions.com.br")
            )
        
        conn.commit()
        print("✅ Tabelas criadas/atualizadas com sucesso")
        return True
        
    except Exception as e:
        print(f"❌ Erro ao criar tabelas: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()


# ========== FUNÇÕES DE USUÁRIOS ==========

def cadastrar_usuario_completo(usuario, senha, perfil, nome_completo, empresa, email):
    """Cadastra novo usuário com senha hash."""
    try:
        conn = conectar()
        cursor = conn.cursor()
        
        # Gerar hash da senha
        senha_hash, salt = hash_senha(senha)
        
        cursor.execute("""
            INSERT INTO usuarios 
            (usuario, senha_hash, salt, perfil, nome_completo, empresa, email)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (usuario, senha_hash, salt, perfil, nome_completo, empresa, email))
        
        conn.commit()
        conn.close()
        return True
        
    except sqlite3.IntegrityError:
        return False
    except Exception as e:
        print(f"Erro ao cadastrar usuário: {e}")
        return False


def listar_usuarios():
    """Lista todos os usuários cadastrados."""
    try:
        conn = conectar()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT id, usuario, perfil, nome_completo, empresa, email, 
                   data_cadastro, ativo
            FROM usuarios
            ORDER BY usuario
        """)
        
        usuarios = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return usuarios
        
    except Exception as e:
        print(f"Erro ao listar usuários: {e}")
        return []


def buscar_usuario_por_id(user_id):
    """Busca usuário por ID."""
    try:
        conn = conectar()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT id, usuario, perfil, nome_completo, empresa, email, ativo
            FROM usuarios
            WHERE id = ?
        """, (user_id,))
        
        usuario = cursor.fetchone()
        conn.close()
        
        return dict(usuario) if usuario else None
        
    except Exception as e:
        print(f"Erro ao buscar usuário: {e}")
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
        """, (dados['nome_completo'], dados['empresa'], dados['email'], 
              dados['perfil'], user_id))
        
        conn.commit()
        conn.close()
        return True
        
    except Exception as e:
        print(f"Erro ao atualizar usuário: {e}")
        return False


def excluir_usuario(user_id):
    """Desativa usuário (soft delete)."""
    try:
        conn = conectar()
        cursor = conn.cursor()
        
        cursor.execute("UPDATE usuarios SET ativo = 0 WHERE id = ?", (user_id,))
        
        conn.commit()
        conn.close()
        return True
        
    except Exception as e:
        print(f"Erro ao excluir usuário: {e}")
        return False


# ========== FUNÇÕES DE CHAMADOS ==========

def buscar_chamados(usuario, perfil):
    """Busca chamados baseado no perfil do usuário."""
    try:
        conn = conectar()
        cursor = conn.cursor()
        
        if perfil == "admin":
            # Admin vê todos os chamados
            cursor.execute("""
                SELECT * FROM chamados
                ORDER BY 
                    CASE status
                        WHEN 'Novo' THEN 1
                        WHEN 'Em atendimento' THEN 2
                        WHEN 'Concluído' THEN 3
                    END,
                    data_abertura DESC
            """)
        else:
            # Outros usuários veem apenas seus chamados
            cursor.execute("""
                SELECT * FROM chamados
                WHERE usuario = ?
                ORDER BY 
                    CASE status
                        WHEN 'Novo' THEN 1
                        WHEN 'Em atendimento' THEN 2
                        WHEN 'Concluído' THEN 3
                    END,
                    data_abertura DESC
            """, (usuario,))
        
        chamados = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return chamados
        
    except Exception as e:
        print(f"Erro ao buscar chamados: {e}")
        return []


def buscar_descricao_chamado(chamado_id):
    """Busca descrição completa de um chamado."""
    try:
        conn = conectar()
        cursor = conn.cursor()
        
        cursor.execute("SELECT descricao FROM chamados WHERE id = ?", (chamado_id,))
        resultado = cursor.fetchone()
        conn.close()
        
        return resultado['descricao'] if resultado else "Descrição não encontrada"
        
    except Exception as e:
        print(f"Erro ao buscar descrição: {e}")
        return "Erro ao carregar descrição"


# ========== FUNÇÕES DE ATENDIMENTO ==========

def iniciar_atendimento_admin(chamado_id, atendente):
    """Admin inicia atendimento de um chamado."""
    try:
        conn = conectar()
        cursor = conn.cursor()
        
        agora = datetime.now()
        
        cursor.execute("""
            UPDATE chamados
            SET status = 'Em atendimento',
                atendente = ?,
                data_inicio_atendimento = ?,
                status_atendimento = 'em_andamento',
                ultima_retomada = ?
            WHERE id = ? AND status = 'Novo'
        """, (atendente, agora, agora, chamado_id))
        
        if cursor.rowcount > 0:
            # Registrar no histórico
            cursor.execute("""
                INSERT INTO historico_atendimento
                (chamado_id, acao, atendente, tempo_acumulado_segundos)
                VALUES (?, 'Iniciou atendimento', ?, 0)
            """, (chamado_id, atendente))
            
            conn.commit()
            conn.close()
            return True, "✅ Atendimento iniciado com sucesso!"
        else:
            conn.close()
            return False, "❌ Não foi possível iniciar o atendimento"
        
    except Exception as e:
        print(f"Erro ao iniciar atendimento: {e}")
        return False, f"Erro: {str(e)}"


def pausar_atendimento(chamado_id):
    """Pausa o cronômetro de atendimento."""
    try:
        conn = conectar()
        cursor = conn.cursor()
        
        # Buscar dados atuais
        cursor.execute("""
            SELECT tempo_atendimento_segundos, ultima_retomada, atendente
            FROM chamados
            WHERE id = ? AND status_atendimento = 'em_andamento'
        """, (chamado_id,))
        
        dados = cursor.fetchone()
        
        if not dados:
            conn.close()
            return False, "Atendimento não está em andamento"
        
        # Calcular tempo decorrido desde última retomada
        tempo_atual = dados['tempo_atendimento_segundos'] or 0
        
        if dados['ultima_retomada']:
            # Remover microsegundos do timestamp
            ultima_retomada_str = str(dados['ultima_retomada']).split('.')[0]
            ultima_retomada = datetime.strptime(ultima_retomada_str, "%Y-%m-%d %H:%M:%S")
            tempo_decorrido = int((datetime.now() - ultima_retomada).total_seconds())
            tempo_atual += tempo_decorrido
        
        # Atualizar para pausado
        cursor.execute("""
            UPDATE chamados
            SET status_atendimento = 'pausado',
                tempo_atendimento_segundos = ?,
                ultima_retomada = NULL
            WHERE id = ?
        """, (tempo_atual, chamado_id))
        
        # Registrar no histórico
        cursor.execute("""
            INSERT INTO historico_atendimento
            (chamado_id, acao, atendente, tempo_acumulado_segundos)
            VALUES (?, 'Pausou atendimento', ?, ?)
        """, (chamado_id, dados['atendente'], tempo_atual))
        
        conn.commit()
        conn.close()
        return True, f"⏸️ Atendimento pausado. Tempo: {formatar_tempo(tempo_atual)}"
        
    except Exception as e:
        print(f"Erro ao pausar atendimento: {e}")
        return False, f"Erro: {str(e)}"


def retomar_atendimento(chamado_id):
    """Retoma o cronômetro de atendimento."""
    try:
        conn = conectar()
        cursor = conn.cursor()
        
        agora = datetime.now()
        
        cursor.execute("""
            SELECT atendente FROM chamados
            WHERE id = ? AND status_atendimento = 'pausado'
        """, (chamado_id,))
        
        dados = cursor.fetchone()
        
        if not dados:
            conn.close()
            return False, "Atendimento não está pausado"
        
        cursor.execute("""
            UPDATE chamados
            SET status_atendimento = 'em_andamento',
                ultima_retomada = ?
            WHERE id = ?
        """, (agora, chamado_id))
        
        # Registrar no histórico
        cursor.execute("""
            INSERT INTO historico_atendimento
            (chamado_id, acao, atendente)
            VALUES (?, 'Retomou atendimento', ?)
        """, (chamado_id, dados['atendente']))
        
        conn.commit()
        conn.close()
        return True, "▶️ Atendimento retomado!"
        
    except Exception as e:
        print(f"Erro ao retomar atendimento: {e}")
        return False, f"Erro: {str(e)}"


def concluir_atendimento_admin(chamado_id):
    """Admin conclui o atendimento do chamado."""
    try:
        conn = conectar()
        cursor = conn.cursor()
        
        # Buscar tempo atual
        cursor.execute("""
            SELECT tempo_atendimento_segundos, ultima_retomada, atendente,
                   status_atendimento
            FROM chamados
            WHERE id = ? AND status = 'Em atendimento'
        """, (chamado_id,))
        
        dados = cursor.fetchone()
        
        if not dados:
            conn.close()
            return False, "Chamado não está em atendimento"
        
        tempo_final = dados['tempo_atendimento_segundos'] or 0
        
        # Se estava em andamento, adicionar tempo decorrido
        if dados['status_atendimento'] == 'em_andamento' and dados['ultima_retomada']:
            # Remover microsegundos do timestamp
            ultima_retomada_str = str(dados['ultima_retomada']).split('.')[0]
            ultima_retomada = datetime.strptime(ultima_retomada_str, "%Y-%m-%d %H:%M:%S")
            tempo_decorrido = int((datetime.now() - ultima_retomada).total_seconds())
            tempo_final += tempo_decorrido
        
        agora = datetime.now()
        
        cursor.execute("""
            UPDATE chamados
            SET status = 'Concluído',
                data_fim_atendimento = ?,
                tempo_atendimento_segundos = ?,
                status_atendimento = 'concluido'
            WHERE id = ?
        """, (agora, tempo_final, chamado_id))
        
        # Registrar no histórico
        cursor.execute("""
            INSERT INTO historico_atendimento
            (chamado_id, acao, atendente, tempo_acumulado_segundos)
            VALUES (?, 'Concluiu atendimento', ?, ?)
        """, (chamado_id, dados['atendente'], tempo_final))
        
        conn.commit()
        conn.close()
        
        return True, f"✅ Atendimento concluído! Tempo total: {formatar_tempo(tempo_final)}"
        
    except Exception as e:
        print(f"Erro ao concluir atendimento: {e}")
        return False, f"Erro: {str(e)}"


def cliente_concluir_chamado(chamado_id, usuario):
    """Cliente marca seu próprio chamado como concluído."""
    try:
        conn = conectar()
        cursor = conn.cursor()
        
        cursor.execute("""
            UPDATE chamados
            SET status = 'Concluído',
                data_fim_atendimento = ?
            WHERE id = ? AND usuario = ? AND status = 'Em atendimento'
        """, (datetime.now(), chamado_id, usuario))
        
        if cursor.rowcount > 0:
            conn.commit()
            conn.close()
            return True, "✅ Chamado marcado como concluído!"
        else:
            conn.close()
            return False, "Não foi possível concluir o chamado"
        
    except Exception as e:
        print(f"Erro ao concluir chamado: {e}")
        return False, f"Erro: {str(e)}"


def obter_tempo_atendimento(chamado_id):
    """Obtém tempo atual de atendimento de um chamado."""
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
        
        # Se está em andamento, adicionar tempo desde última retomada
        if dados['status_atendimento'] == 'em_andamento' and dados['ultima_retomada']:
            try:
                # Remover microsegundos do timestamp
                ultima_retomada_str = str(dados['ultima_retomada']).split('.')[0]
                ultima_retomada = datetime.strptime(ultima_retomada_str, "%Y-%m-%d %H:%M:%S")
                tempo_decorrido = int((datetime.now() - ultima_retomada).total_seconds())
                tempo_atual += tempo_decorrido
            except Exception as e:
                print(f"Erro ao calcular tempo decorrido: {e}")
        
        return tempo_atual
        
    except Exception as e:
        print(f"Erro ao obter tempo: {e}")
        return 0


# ========== FUNÇÕES DE ANEXOS ==========

def salvar_anexo(chamado_id, nome_arquivo, caminho_arquivo):
    """Salva informações de anexo no banco."""
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
        
    except Exception as e:
        print(f"Erro ao salvar anexo: {e}")
        return False


def buscar_anexos(chamado_id):
    """Busca todos os anexos de um chamado."""
    try:
        conn = conectar()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT * FROM anexos
            WHERE chamado_id = ?
            ORDER BY data_upload DESC
        """, (chamado_id,))
        
        anexos = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return anexos
        
    except Exception as e:
        print(f"Erro ao buscar anexos: {e}")
        return []


def excluir_anexo(anexo_id):
    """Exclui um anexo do banco."""
    try:
        conn = conectar()
        cursor = conn.cursor()
        
        # Buscar caminho do arquivo primeiro
        cursor.execute("SELECT caminho_arquivo FROM anexos WHERE id = ?", (anexo_id,))
        resultado = cursor.fetchone()
        
        if resultado:
            caminho = resultado['caminho_arquivo']
            
            # Excluir arquivo físico
            if os.path.exists(caminho):
                os.remove(caminho)
            
            # Excluir do banco
            cursor.execute("DELETE FROM anexos WHERE id = ?", (anexo_id,))
            conn.commit()
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"Erro ao excluir anexo: {e}")
        return False


# ========== FUNÇÕES DE ESTATÍSTICAS ==========

def buscar_estatisticas_usuario(usuario, perfil):
    """Busca estatísticas baseadas no perfil."""
    try:
        conn = conectar()
        cursor = conn.cursor()
        
        if perfil == "admin":
            # Admin vê estatísticas de todos
            cursor.execute("SELECT COUNT(*) as total FROM chamados")
            total = cursor.fetchone()['total']
            
            cursor.execute("SELECT COUNT(*) as novos FROM chamados WHERE status = 'Novo'")
            novos = cursor.fetchone()['novos']
            
            cursor.execute("SELECT COUNT(*) as em_atendimento FROM chamados WHERE status = 'Em atendimento'")
            em_atendimento = cursor.fetchone()['em_atendimento']
            
            cursor.execute("SELECT COUNT(*) as concluidos FROM chamados WHERE status = 'Concluído'")
            concluidos = cursor.fetchone()['concluidos']
        else:
            # Outros veem apenas seus chamados
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
        
    except Exception as e:
        print(f"Erro ao buscar estatísticas: {e}")
        return {
            "total": 0,
            "novos": 0,
            "em_atendimento": 0,
            "concluidos": 0
        }
