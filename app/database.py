# app/database.py
"""
Banco de Dados do Sistema Helpdesk
TODAS as informações são persistidas aqui:
- Usuários
- Chamados
- Anexos
- Interações
- Mensagens de conclusão
- Logs do sistema
- Downloads
"""

import sqlite3
import os
from datetime import datetime
from utils import hash_senha, formatar_tempo, parse_datetime_safe, agora_brasilia_str

# ========== CONEXÃO ==========

def conectar():
    """Conecta ao banco de dados SQLite."""
    if not os.path.exists("data"):
        os.makedirs("data")
    
    conn = sqlite3.connect("data/database.db", check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("PRAGMA journal_mode = WAL")  # Melhor para concorrência
    return conn

# ========== CRIAÇÃO DE TABELAS ==========

def criar_tabelas():
    """Cria TODAS as tabelas necessárias para persistência completa."""
    conn = conectar()
    cursor = conn.cursor()
    
    try:
        # ========== TABELA DE USUÁRIOS ==========
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
                ultimo_acesso TIMESTAMP,
                ativo INTEGER DEFAULT 1
            )
        """)
        
        # ========== TABELA DE CHAMADOS ==========
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
                ultima_retomada TIMESTAMP,
                retornos INTEGER DEFAULT 0,
                data_ultima_atualizacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # ========== TABELA DE ANEXOS (arquivos enviados na abertura) ==========
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS anexos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                chamado_id INTEGER NOT NULL,
                nome_arquivo TEXT NOT NULL,
                caminho_arquivo TEXT NOT NULL,
                tamanho_bytes INTEGER,
                tipo_arquivo TEXT,
                data_upload TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (chamado_id) REFERENCES chamados(id) ON DELETE CASCADE
            )
        """)
        
        # ========== TABELA DE INTERAÇÕES (conversas no chamado) ==========
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS interacoes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                chamado_id INTEGER NOT NULL,
                autor TEXT NOT NULL,
                mensagem TEXT NOT NULL,
                tipo TEXT DEFAULT 'mensagem',
                data TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                enviar_email INTEGER DEFAULT 1,
                email_enviado INTEGER DEFAULT 0,
                FOREIGN KEY (chamado_id) REFERENCES chamados(id) ON DELETE CASCADE
            )
        """)
        
        # ========== TABELA DE ANEXOS DE INTERAÇÃO ==========
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS anexos_interacao (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                interacao_id INTEGER NOT NULL,
                nome_arquivo TEXT NOT NULL,
                caminho_arquivo TEXT NOT NULL,
                tamanho_bytes INTEGER,
                tipo_arquivo TEXT,
                data_upload TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (interacao_id) REFERENCES interacoes(id) ON DELETE CASCADE
            )
        """)
        
        # ========== TABELA DE MENSAGENS DE CONCLUSÃO ==========
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS mensagens_conclusao (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                chamado_id INTEGER NOT NULL,
                mensagem TEXT NOT NULL,
                atendente TEXT NOT NULL,
                data_envio TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (chamado_id) REFERENCES chamados(id) ON DELETE CASCADE
            )
        """)
        
        # ========== TABELA DE ANEXOS DE CONCLUSÃO ==========
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS anexos_conclusao (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                mensagem_id INTEGER NOT NULL,
                nome_arquivo TEXT NOT NULL,
                caminho_arquivo TEXT NOT NULL,
                tamanho_bytes INTEGER,
                FOREIGN KEY (mensagem_id) REFERENCES mensagens_conclusao(id) ON DELETE CASCADE
            )
        """)
        
        # ========== TABELA DE LOGS DO SISTEMA ==========
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS logs_sistema (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                acao TEXT NOT NULL,
                usuario TEXT,
                detalhes TEXT,
                ip_address TEXT,
                data_hora TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # ========== TABELA DE DOWNLOADS ==========
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS downloads (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                usuario TEXT NOT NULL,
                arquivo_nome TEXT NOT NULL,
                arquivo_caminho TEXT NOT NULL,
                chamado_id INTEGER,
                data_download TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (chamado_id) REFERENCES chamados(id) ON DELETE SET NULL
            )
        """)
        
        # ========== TABELA DE SESSÕES ==========
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS sessoes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                usuario TEXT NOT NULL,
                token TEXT UNIQUE NOT NULL,
                data_inicio TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                data_ultimo_acesso TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                ip_address TEXT,
                ativo INTEGER DEFAULT 1
            )
        """)
        
        # ========== TABELA DE EMAILS ENVIADOS ==========
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS emails_enviados (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                destinatario TEXT NOT NULL,
                assunto TEXT NOT NULL,
                corpo TEXT,
                chamado_id INTEGER,
                tipo TEXT,
                sucesso INTEGER DEFAULT 0,
                erro TEXT,
                data_envio TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (chamado_id) REFERENCES chamados(id) ON DELETE SET NULL
            )
        """)
        
        # ========== CRIAR ÍNDICES PARA PERFORMANCE ==========
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_chamados_usuario ON chamados(usuario)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_chamados_status ON chamados(status)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_interacoes_chamado ON interacoes(chamado_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_anexos_chamado ON anexos(chamado_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_logs_usuario ON logs_sistema(usuario)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_logs_data ON logs_sistema(data_hora)")
        
        # ========== CRIAR USUÁRIO ADMIN PADRÃO ==========
        cursor.execute("SELECT COUNT(*) FROM usuarios WHERE usuario = 'admin'")
        if cursor.fetchone()[0] == 0:
            senha_hash, salt = hash_senha("admin123")
            cursor.execute("""
                INSERT INTO usuarios 
                (usuario, senha_hash, salt, perfil, nome_completo, empresa, email, data_cadastro)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, ("admin", senha_hash, salt, "admin", "Administrador", "MP Solutions", "admin@mp.com", agora_brasilia_str()))
        
        conn.commit()
        
        # Registrar criação das tabelas
        registrar_log_db(cursor, "SISTEMA", "admin", "Tabelas criadas/verificadas com sucesso")
        conn.commit()
        
        return True
    except Exception as e:
        print(f"Erro ao criar tabelas: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()

def registrar_log_db(cursor, acao, usuario, detalhes=""):
    """Registra log no banco (usar dentro de transação existente)."""
    try:
        cursor.execute("""
            INSERT INTO logs_sistema (acao, usuario, detalhes, data_hora)
            VALUES (?, ?, ?, ?)
        """, (acao, usuario, detalhes, agora_brasilia_str()))
    except:
        pass

# ========== FUNÇÕES DE LOG ==========

def registrar_log(acao, usuario, detalhes="", ip_address=None):
    """Registra ação no log do sistema."""
    try:
        conn = conectar()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO logs_sistema (acao, usuario, detalhes, ip_address, data_hora)
            VALUES (?, ?, ?, ?, ?)
        """, (acao, usuario, detalhes, ip_address, agora_brasilia_str()))
        conn.commit()
        conn.close()
        return True
    except:
        return False

def registrar_download(usuario, arquivo_nome, arquivo_caminho, chamado_id=None):
    """Registra download de arquivo."""
    try:
        conn = conectar()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO downloads (usuario, arquivo_nome, arquivo_caminho, chamado_id, data_download)
            VALUES (?, ?, ?, ?, ?)
        """, (usuario, arquivo_nome, arquivo_caminho, chamado_id, agora_brasilia_str()))
        conn.commit()
        conn.close()
        registrar_log("DOWNLOAD", usuario, f"Baixou: {arquivo_nome}")
        return True
    except:
        return False

def registrar_email_enviado(destinatario, assunto, corpo, chamado_id, tipo, sucesso, erro=None):
    """Registra email enviado no banco."""
    try:
        conn = conectar()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO emails_enviados (destinatario, assunto, corpo, chamado_id, tipo, sucesso, erro, data_envio)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (destinatario, assunto, corpo[:500] if corpo else None, chamado_id, tipo, 1 if sucesso else 0, erro, agora_brasilia_str()))
        conn.commit()
        conn.close()
        return True
    except:
        return False

# ========== USUÁRIOS ==========

def cadastrar_usuario_completo(usuario, senha, perfil, nome_completo, empresa, email):
    """Cadastra novo usuário."""
    try:
        conn = conectar()
        cursor = conn.cursor()
        
        senha_hash, salt = hash_senha(senha)
        
        cursor.execute("""
            INSERT INTO usuarios 
            (usuario, senha_hash, salt, perfil, nome_completo, empresa, email, data_cadastro)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (usuario, senha_hash, salt, perfil, nome_completo, empresa, email, agora_brasilia_str()))
        
        conn.commit()
        registrar_log("CADASTRO_USUARIO", usuario, f"Novo usuário: {usuario} ({perfil})")
        conn.close()
        return True
    except Exception as e:
        print(f"Erro ao cadastrar usuário: {e}")
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

def buscar_usuario_por_nome(usuario):
    """Busca usuário pelo nome de usuário."""
    try:
        conn = conectar()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM usuarios WHERE usuario = ?", (usuario,))
        resultado = cursor.fetchone()
        conn.close()
        return dict(resultado) if resultado else None
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
        registrar_log("ATUALIZAR_USUARIO", dados.get('usuario', 'admin'), f"Usuário ID {user_id} atualizado")
        conn.close()
        return True
    except:
        return False

def excluir_usuario(user_id):
    """Desativa usuário (não exclui para manter histórico)."""
    try:
        conn = conectar()
        cursor = conn.cursor()
        cursor.execute("UPDATE usuarios SET ativo = 0 WHERE id = ?", (user_id,))
        conn.commit()
        registrar_log("DESATIVAR_USUARIO", "admin", f"Usuário ID {user_id} desativado")
        conn.close()
        return True
    except:
        return False

def atualizar_ultimo_acesso(usuario):
    """Atualiza último acesso do usuário."""
    try:
        conn = conectar()
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE usuarios SET ultimo_acesso = ? WHERE usuario = ?
        """, (agora_brasilia_str(), usuario))
        conn.commit()
        conn.close()
        return True
    except:
        return False

# ========== CHAMADOS ==========

def criar_chamado(assunto, prioridade, descricao, usuario):
    """Cria novo chamado."""
    try:
        conn = conectar()
        cursor = conn.cursor()
        
        agora = agora_brasilia_str()
        
        cursor.execute("""
            INSERT INTO chamados
            (assunto, prioridade, descricao, status, usuario, data_abertura, data_ultima_atualizacao)
            VALUES (?, ?, ?, 'Novo', ?, ?, ?)
        """, (assunto, prioridade, descricao, usuario, agora, agora))
        
        chamado_id = cursor.lastrowid
        conn.commit()
        
        registrar_log("NOVO_CHAMADO", usuario, f"Chamado #{chamado_id} criado: {assunto}")
        conn.close()
        
        return chamado_id
    except Exception as e:
        print(f"Erro ao criar chamado: {e}")
        return None

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

def buscar_chamado_por_id(chamado_id):
    """Busca chamado por ID."""
    try:
        conn = conectar()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM chamados WHERE id = ?", (chamado_id,))
        chamado = cursor.fetchone()
        conn.close()
        return dict(chamado) if chamado else None
    except:
        return None

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

def atualizar_status_chamado(chamado_id, novo_status):
    """Atualiza status do chamado."""
    try:
        conn = conectar()
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE chamados 
            SET status = ?, data_ultima_atualizacao = ?
            WHERE id = ?
        """, (novo_status, agora_brasilia_str(), chamado_id))
        conn.commit()
        registrar_log("ATUALIZAR_STATUS", "sistema", f"Chamado #{chamado_id} -> {novo_status}")
        conn.close()
        return True
    except:
        return False

# ========== ATENDIMENTO ==========

def iniciar_atendimento_admin(chamado_id, atendente):
    """Admin inicia atendimento."""
    try:
        conn = conectar()
        cursor = conn.cursor()
        
        agora = agora_brasilia_str()
        
        cursor.execute("""
            UPDATE chamados
            SET status = 'Em atendimento',
                atendente = ?,
                data_inicio_atendimento = ?,
                status_atendimento = 'em_andamento',
                ultima_retomada = ?,
                tempo_atendimento_segundos = 0,
                data_ultima_atualizacao = ?
            WHERE id = ? AND status = 'Novo'
        """, (atendente, agora, agora, agora, chamado_id))
        
        if cursor.rowcount > 0:
            conn.commit()
            registrar_log("INICIAR_ATENDIMENTO", atendente, f"Chamado #{chamado_id}")
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
                from utils import agora_brasilia
                tempo_decorrido = int((agora_brasilia().replace(tzinfo=None) - ultima_retomada).total_seconds())
                tempo_atual += tempo_decorrido
        
        cursor.execute("""
            UPDATE chamados
            SET status_atendimento = 'pausado',
                tempo_atendimento_segundos = ?,
                ultima_retomada = NULL,
                data_ultima_atualizacao = ?
            WHERE id = ?
        """, (tempo_atual, agora_brasilia_str(), chamado_id))
        
        conn.commit()
        registrar_log("PAUSAR_ATENDIMENTO", "admin", f"Chamado #{chamado_id} - Tempo: {formatar_tempo(tempo_atual)}")
        conn.close()
        return True, f"⏸️ Pausado. Tempo: {formatar_tempo(tempo_atual)}"
    except Exception as e:
        return False, f"Erro: {e}"

def retomar_atendimento(chamado_id):
    """Retoma o cronômetro."""
    try:
        conn = conectar()
        cursor = conn.cursor()
        
        agora = agora_brasilia_str()
        
        cursor.execute("""
            UPDATE chamados
            SET status_atendimento = 'em_andamento',
                ultima_retomada = ?,
                data_ultima_atualizacao = ?
            WHERE id = ? AND status_atendimento = 'pausado'
        """, (agora, agora, chamado_id))
        
        if cursor.rowcount > 0:
            conn.commit()
            registrar_log("RETOMAR_ATENDIMENTO", "admin", f"Chamado #{chamado_id}")
            conn.close()
            return True, "▶️ Retomado!"
        else:
            conn.close()
            return False, "Não está pausado"
    except Exception as e:
        return False, f"Erro: {e}"

def concluir_atendimento_admin(chamado_id, mensagem_conclusao=None, arquivos_conclusao=None):
    """Admin conclui o atendimento com mensagem opcional."""
    try:
        conn = conectar()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT tempo_atendimento_segundos, ultima_retomada, status_atendimento, atendente
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
                from utils import agora_brasilia
                tempo_decorrido = int((agora_brasilia().replace(tzinfo=None) - ultima_retomada).total_seconds())
                tempo_final += tempo_decorrido
        
        agora = agora_brasilia_str()
        
        cursor.execute("""
            UPDATE chamados
            SET status = 'Aguardando Finalização',
                data_fim_atendimento = ?,
                tempo_atendimento_segundos = ?,
                status_atendimento = 'concluido',
                data_ultima_atualizacao = ?
            WHERE id = ?
        """, (agora, tempo_final, agora, chamado_id))
        
        if mensagem_conclusao:
            cursor.execute("""
                INSERT INTO mensagens_conclusao (chamado_id, mensagem, atendente, data_envio)
                VALUES (?, ?, ?, ?)
            """, (chamado_id, mensagem_conclusao, dados['atendente'], agora))
            
            mensagem_id = cursor.lastrowid
            
            if arquivos_conclusao:
                for arquivo_info in arquivos_conclusao:
                    cursor.execute("""
                        INSERT INTO anexos_conclusao (mensagem_id, nome_arquivo, caminho_arquivo)
                        VALUES (?, ?, ?)
                    """, (mensagem_id, arquivo_info['nome'], arquivo_info['caminho']))
        
        conn.commit()
        registrar_log("CONCLUIR_ATENDIMENTO", dados['atendente'], f"Chamado #{chamado_id} - Tempo: {formatar_tempo(tempo_final)}")
        conn.close()
        
        return True, f"✅ Atendimento concluído! Tempo: {formatar_tempo(tempo_final)}"
    except Exception as e:
        return False, f"Erro: {e}"

def cliente_concluir_chamado(chamado_id, usuario):
    """Cliente marca como concluído."""
    try:
        conn = conectar()
        cursor = conn.cursor()
        
        agora = agora_brasilia_str()
        
        cursor.execute("""
            UPDATE chamados
            SET status = 'Concluído',
                data_fim_atendimento = ?,
                data_ultima_atualizacao = ?
            WHERE id = ? AND usuario = ?
        """, (agora, agora, chamado_id, usuario))
        
        if cursor.rowcount > 0:
            conn.commit()
            registrar_log("CLIENTE_CONCLUIR", usuario, f"Chamado #{chamado_id}")
            conn.close()
            return True, "✅ Marcado como concluído!"
        else:
            conn.close()
            return False, "Erro"
    except Exception as e:
        return False, f"Erro: {e}"

def finalizar_chamado_cliente(chamado_id, usuario):
    """Cliente finaliza definitivamente o chamado."""
    try:
        conn = conectar()
        cursor = conn.cursor()
        
        agora = agora_brasilia_str()
        
        cursor.execute("""
            UPDATE chamados
            SET status = 'Finalizado',
                data_ultima_atualizacao = ?
            WHERE id = ? AND usuario = ? AND status = 'Aguardando Finalização'
        """, (agora, chamado_id, usuario))
        
        if cursor.rowcount > 0:
            conn.commit()
            registrar_log("FINALIZAR_CHAMADO", usuario, f"Chamado #{chamado_id} finalizado pelo cliente")
            conn.close()
            return True, "✅ Chamado finalizado com sucesso!"
        else:
            conn.close()
            return False, "❌ Não foi possível finalizar"
    except Exception as e:
        return False, f"Erro: {e}"

def retornar_chamado(chamado_id, usuario, mensagem_retorno):
    """Cliente retorna chamado para atendimento."""
    try:
        conn = conectar()
        cursor = conn.cursor()
        
        agora = agora_brasilia_str()
        
        # Incrementar contador de retornos
        cursor.execute("""
            UPDATE chamados
            SET status = 'Em atendimento',
                status_atendimento = 'em_andamento',
                ultima_retomada = ?,
                retornos = retornos + 1,
                data_ultima_atualizacao = ?
            WHERE id = ? AND usuario = ? AND status = 'Aguardando Finalização'
        """, (agora, agora, chamado_id, usuario))
        
        if cursor.rowcount > 0:
            # Registrar interação de retorno
            cursor.execute("""
                INSERT INTO interacoes (chamado_id, autor, mensagem, tipo, data)
                VALUES (?, 'cliente', ?, 'retorno', ?)
            """, (chamado_id, mensagem_retorno, agora))
            
            conn.commit()
            registrar_log("RETORNAR_CHAMADO", usuario, f"Chamado #{chamado_id} retornado")
            conn.close()
            return True, "🔄 Chamado retornado para atendimento!"
        else:
            conn.close()
            return False, "❌ Não foi possível retornar"
    except Exception as e:
        return False, f"Erro: {e}"

def retornar_chamado_admin(chamado_id, atendente, mensagem_retorno, arquivos=None):
    """Admin retorna chamado para o cliente com anexos opcionais."""
    try:
        conn = conectar()
        cursor = conn.cursor()
        
        agora = agora_brasilia_str()
        
        cursor.execute("""
            UPDATE chamados
            SET status = 'Aguardando Cliente',
                data_ultima_atualizacao = ?
            WHERE id = ?
        """, (agora, chamado_id))
        
        # Registrar interação
        cursor.execute("""
            INSERT INTO interacoes (chamado_id, autor, mensagem, tipo, data, enviar_email)
            VALUES (?, 'atendente', ?, 'retorno_admin', ?, 1)
        """, (chamado_id, mensagem_retorno, agora))
        
        interacao_id = cursor.lastrowid
        
        # Salvar anexos se houver
        if arquivos:
            for arquivo_info in arquivos:
                cursor.execute("""
                    INSERT INTO anexos_interacao (interacao_id, nome_arquivo, caminho_arquivo, tamanho_bytes, data_upload)
                    VALUES (?, ?, ?, ?, ?)
                """, (interacao_id, arquivo_info['nome'], arquivo_info['caminho'], arquivo_info.get('tamanho', 0), agora))
        
        conn.commit()
        registrar_log("RETORNO_ADMIN", atendente, f"Chamado #{chamado_id} retornado ao cliente")
        conn.close()
        
        return True, "✅ Chamado retornado ao cliente!"
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
                from utils import agora_brasilia
                tempo_decorrido = int((agora_brasilia().replace(tzinfo=None) - ultima_retomada).total_seconds())
                tempo_atual += tempo_decorrido
        
        return tempo_atual
    except:
        return 0

# ========== INTERAÇÕES ==========

def adicionar_interacao_chamado(chamado_id, autor, mensagem, tipo='mensagem'):
    """Adiciona interação ao chamado."""
    try:
        conn = conectar()
        cursor = conn.cursor()
        
        agora = agora_brasilia_str()
        
        cursor.execute("""
            INSERT INTO interacoes (chamado_id, autor, mensagem, tipo, data, enviar_email)
            VALUES (?, ?, ?, ?, ?, 1)
        """, (chamado_id, autor, mensagem, tipo, agora))
        
        interacao_id = cursor.lastrowid
        
        # Atualizar data do chamado
        cursor.execute("""
            UPDATE chamados SET data_ultima_atualizacao = ? WHERE id = ?
        """, (agora, chamado_id))
        
        conn.commit()
        registrar_log("NOVA_INTERACAO", autor, f"Chamado #{chamado_id}")
        conn.close()
        
        return True, interacao_id
    except Exception as e:
        return False, f"Erro: {e}"

def buscar_interacoes_chamado(chamado_id):
    """Busca interações de um chamado."""
    try:
        conn = conectar()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT * FROM interacoes 
            WHERE chamado_id = ? 
            ORDER BY data ASC
        """, (chamado_id,))
        interacoes = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return interacoes
    except:
        return []

def buscar_anexos_interacao(interacao_id):
    """Busca anexos de uma interação."""
    try:
        conn = conectar()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT * FROM anexos_interacao 
            WHERE interacao_id = ?
        """, (interacao_id,))
        anexos = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return anexos
    except:
        return []

# ========== ANEXOS ==========

def salvar_anexo(chamado_id, nome_arquivo, caminho_arquivo, tamanho=None, tipo=None):
    """Salva anexo no banco."""
    try:
        conn = conectar()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO anexos (chamado_id, nome_arquivo, caminho_arquivo, tamanho_bytes, tipo_arquivo, data_upload)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (chamado_id, nome_arquivo, caminho_arquivo, tamanho, tipo, agora_brasilia_str()))
        conn.commit()
        registrar_log("ANEXO_ADICIONADO", "sistema", f"Chamado #{chamado_id}: {nome_arquivo}")
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
        registrar_log("ANEXO_EXCLUIDO", "admin", f"Anexo ID {anexo_id}")
        conn.close()
        return True
    except:
        return False

# ========== MENSAGENS DE CONCLUSÃO ==========

def buscar_mensagem_conclusao(chamado_id):
    """Busca mensagem de conclusão do chamado."""
    try:
        conn = conectar()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT m.*, GROUP_CONCAT(a.nome_arquivo) as arquivos
            FROM mensagens_conclusao m
            LEFT JOIN anexos_conclusao a ON m.id = a.mensagem_id
            WHERE m.chamado_id = ?
            GROUP BY m.id
            ORDER BY m.data_envio DESC
            LIMIT 1
        """, (chamado_id,))
        
        resultado = cursor.fetchone()
        conn.close()
        
        return dict(resultado) if resultado else None
    except:
        return None

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
            cursor.execute("SELECT COUNT(*) as concluidos FROM chamados WHERE status = 'Finalizado'")
            concluidos = cursor.fetchone()['concluidos']
        else:
            cursor.execute("SELECT COUNT(*) as total FROM chamados WHERE usuario = ?", (usuario,))
            total = cursor.fetchone()['total']
            cursor.execute("SELECT COUNT(*) as novos FROM chamados WHERE usuario = ? AND status = 'Novo'", (usuario,))
            novos = cursor.fetchone()['novos']
            cursor.execute("SELECT COUNT(*) as em_atendimento FROM chamados WHERE usuario = ? AND status = 'Em atendimento'", (usuario,))
            em_atendimento = cursor.fetchone()['em_atendimento']
            cursor.execute("SELECT COUNT(*) as concluidos FROM chamados WHERE usuario = ? AND status = 'Finalizado'", (usuario,))
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

def buscar_logs_sistema(limite=100, usuario=None):
    """Busca logs do sistema."""
    try:
        conn = conectar()
        cursor = conn.cursor()
        
        if usuario:
            cursor.execute("""
                SELECT * FROM logs_sistema 
                WHERE usuario = ?
                ORDER BY data_hora DESC 
                LIMIT ?
            """, (usuario, limite))
        else:
            cursor.execute("""
                SELECT * FROM logs_sistema 
                ORDER BY data_hora DESC 
                LIMIT ?
            """, (limite,))
        
        logs = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return logs
    except:
        return []

def buscar_downloads_usuario(usuario, limite=50):
    """Busca downloads de um usuário."""
    try:
        conn = conectar()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT * FROM downloads 
            WHERE usuario = ?
            ORDER BY data_download DESC 
            LIMIT ?
        """, (usuario, limite))
        downloads = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return downloads
    except:
        return []
