# app/utils.py
import hashlib
import secrets
import os
from datetime import datetime
import time
import streamlit as st

# ========== SEGURANÇA DE SENHAS ==========

def hash_senha(senha, salt=None):
    """
    Cria hash seguro da senha usando PBKDF2.
    
    Args:
        senha: Senha em texto plano
        salt: Salt opcional (gerado automaticamente se não fornecido)
    
    Returns:
        tuple: (hash, salt)
    """
    if not salt:
        salt = secrets.token_hex(16)
    
    # PBKDF2 com 100.000 iterações
    hash_obj = hashlib.pbkdf2_hmac(
        'sha256',
        senha.encode('utf-8'),
        salt.encode('utf-8'),
        100000
    )
    
    return hash_obj.hex(), salt


def verificar_senha(senha, hash_armazenado, salt):
    """
    Verifica se a senha corresponde ao hash armazenado.
    
    Args:
        senha: Senha em texto plano
        hash_armazenado: Hash armazenado no banco
        salt: Salt usado na criação do hash
    
    Returns:
        bool: True se a senha estiver correta
    """
    hash_calculado, _ = hash_senha(senha, salt)
    return hash_calculado == hash_armazenado


# ========== VALIDAÇÃO DE ARQUIVOS ==========

TAMANHO_MAX_ARQUIVO = 10 * 1024 * 1024  # 10 MB
EXTENSOES_PERMITIDAS = {
    '.pdf', '.doc', '.docx', '.txt', '.xlsx', '.xls',
    '.jpg', '.jpeg', '.png', '.gif', '.zip', '.rar'
}


def validar_arquivo(arquivo):
    """
    Valida tamanho e tipo de arquivo.
    
    Args:
        arquivo: Objeto de arquivo do Streamlit
    
    Returns:
        tuple: (valido, mensagem_erro)
    """
    if arquivo is None:
        return False, "Nenhum arquivo selecionado"
    
    # Verificar tamanho
    arquivo.seek(0, os.SEEK_END)
    tamanho = arquivo.tell()
    arquivo.seek(0)
    
    if tamanho > TAMANHO_MAX_ARQUIVO:
        return False, f"Arquivo muito grande. Máximo: 10 MB"
    
    # Verificar extensão
    nome_arquivo = arquivo.name.lower()
    extensao = os.path.splitext(nome_arquivo)[1]
    
    if extensao not in EXTENSOES_PERMITIDAS:
        return False, f"Tipo de arquivo não permitido: {extensao}"
    
    return True, "OK"


def gerar_nome_arquivo_seguro(nome_original):
    """
    Gera nome de arquivo único e seguro.
    
    Args:
        nome_original: Nome original do arquivo
    
    Returns:
        str: Nome seguro único
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    nome_limpo = "".join(c for c in nome_original if c.isalnum() or c in "._- ")
    uuid_parte = secrets.token_hex(4)
    
    nome, extensao = os.path.splitext(nome_limpo)
    return f"{timestamp}_{uuid_parte}_{nome}{extensao}"


# ========== CONTROLE DE SESSÃO ==========

TIMEOUT_SESSAO = 1800  # 30 minutos


def verificar_timeout_sessao():
    """
    Verifica se a sessão expirou por inatividade.
    Faz logout automático se necessário.
    """
    if 'usuario' not in st.session_state or st.session_state.usuario is None:
        return
    
    if 'last_activity' not in st.session_state:
        st.session_state.last_activity = time.time()
        return
    
    tempo_inativo = time.time() - st.session_state.last_activity
    
    if tempo_inativo > TIMEOUT_SESSAO:
        st.session_state.clear()
        st.warning("⚠️ Sessão expirada por inatividade. Faça login novamente.")
        st.rerun()
    else:
        # Atualizar timestamp de atividade
        st.session_state.last_activity = time.time()


# ========== FORMATAÇÃO E UTILIDADES ==========

def formatar_tempo(segundos):
    """
    Formata segundos em formato legível (HH:MM:SS).
    
    Args:
        segundos: Tempo em segundos
    
    Returns:
        str: Tempo formatado
    """
    if segundos is None:
        return "00:00:00"
    
    horas = segundos // 3600
    minutos = (segundos % 3600) // 60
    segs = segundos % 60
    
    return f"{int(horas):02d}:{int(minutos):02d}:{int(segs):02d}"


def formatar_data_br(data_str):
    """
    Formata data para padrão brasileiro.
    
    Args:
        data_str: Data no formato YYYY-MM-DD HH:MM:SS ou com microsegundos
    
    Returns:
        str: Data formatada DD/MM/YYYY HH:MM
    """
    try:
        # Remover microsegundos se existirem
        if '.' in data_str:
            data_str = data_str.split('.')[0]
        
        data = datetime.strptime(data_str, "%Y-%m-%d %H:%M:%S")
        return data.strftime("%d/%m/%Y %H:%M")
    except:
        return data_str


def parse_datetime(data_str):
    """
    Converte string de data para datetime, tratando microsegundos.
    
    Args:
        data_str: Data em string
    
    Returns:
        datetime: Objeto datetime
    """
    if not data_str:
        return None
    
    try:
        # Remover microsegundos se existirem
        if '.' in data_str:
            data_str = data_str.split('.')[0]
        
        return datetime.strptime(data_str, "%Y-%m-%d %H:%M:%S")
    except:
        return None


def badge_status(status):
    """
    Retorna emoji/badge para status do chamado.
    
    Args:
        status: Status do chamado
    
    Returns:
        str: Emoji correspondente
    """
    badges = {
        "Novo": "🔴",
        "Em atendimento": "🟡",
        "Concluído": "🟢",
        "Cancelado": "⚫"
    }
    return badges.get(status, "⚪")


def badge_prioridade(prioridade):
    """
    Retorna emoji/badge para prioridade.
    
    Args:
        prioridade: Prioridade do chamado
    
    Returns:
        str: Emoji correspondente
    """
    badges = {
        "Baixa": "🟢",
        "Média": "🟡",
        "Alta": "🟠",
        "Urgente": "🔴"
    }
    return badges.get(prioridade, "⚪")


# ========== VALIDAÇÕES ==========

def validar_email(email):
    """
    Valida formato de email.
    
    Args:
        email: String de email
    
    Returns:
        bool: True se válido
    """
    import re
    padrao = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(padrao, email) is not None


def validar_senha_forte(senha):
    """
    Valida se a senha é forte o suficiente.
    
    Args:
        senha: Senha para validar
    
    Returns:
        tuple: (valido, mensagem)
    """
    if len(senha) < 8:
        return False, "Senha deve ter no mínimo 8 caracteres"
    
    if not any(c.isupper() for c in senha):
        return False, "Senha deve conter pelo menos uma letra maiúscula"
    
    if not any(c.islower() for c in senha):
        return False, "Senha deve conter pelo menos uma letra minúscula"
    
    if not any(c.isdigit() for c in senha):
        return False, "Senha deve conter pelo menos um número"
    
    return True, "Senha válida"


# ========== LOGGING E AUDITORIA ==========

def registrar_log(acao, usuario, detalhes=""):
    """
    Registra ação do usuário para auditoria.
    
    Args:
        acao: Tipo de ação realizada
        usuario: Usuário que realizou a ação
        detalhes: Detalhes adicionais
    """
    from database import conectar
    
    try:
        conn = conectar()
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO logs_auditoria 
            (acao, usuario, detalhes, data_hora)
            VALUES (?, ?, ?, ?)
        """, (acao, usuario, detalhes, datetime.now()))
        
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"Erro ao registrar log: {e}")


# ========== SANITIZAÇÃO ==========

def sanitizar_texto(texto):
    """
    Remove caracteres perigosos de texto.
    
    Args:
        texto: Texto para sanitizar
    
    Returns:
        str: Texto limpo
    """
    if not texto:
        return ""
    
    # Remove tags HTML básicas
    import re
    texto = re.sub(r'<[^>]+>', '', texto)
    
    # Remove caracteres de controle
    texto = ''.join(char for char in texto if ord(char) >= 32 or char in '\n\r\t')
    
    return texto.strip()
