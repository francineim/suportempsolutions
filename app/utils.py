# app/utils.py
import hashlib
import secrets
import os
from datetime import datetime
import re

# ========== SEGURANÇA DE SENHAS ==========

def hash_senha(senha, salt=None):
    """Cria hash seguro da senha."""
    if not salt:
        salt = secrets.token_hex(16)
    hash_obj = hashlib.pbkdf2_hmac('sha256', senha.encode('utf-8'), salt.encode('utf-8'), 100000)
    return hash_obj.hex(), salt

def verificar_senha(senha, hash_armazenado, salt):
    """Verifica se a senha corresponde ao hash."""
    hash_calculado, _ = hash_senha(senha, salt)
    return hash_calculado == hash_armazenado

# ========== VALIDAÇÃO DE ARQUIVOS ==========

def validar_arquivo(arquivo):
    """Valida tamanho e tipo de arquivo."""
    if arquivo is None:
        return False, "Nenhum arquivo selecionado"
    
    arquivo.seek(0, os.SEEK_END)
    tamanho = arquivo.tell()
    arquivo.seek(0)
    
    if tamanho > 10 * 1024 * 1024:
        return False, "Arquivo muito grande. Máximo: 10 MB"
    
    return True, "OK"

def gerar_nome_arquivo_seguro(nome_original):
    """Gera nome de arquivo único e seguro."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    uuid_parte = secrets.token_hex(4)
    nome_limpo = "".join(c for c in nome_original if c.isalnum() or c in "._- ")
    nome, extensao = os.path.splitext(nome_limpo)
    return f"{timestamp}_{uuid_parte}_{nome}{extensao}"

# ========== FORMATAÇÃO ==========

def formatar_tempo(segundos):
    """
    Formata segundos em HH:MM:SS para exibição.
    Backend armazena em segundos (int).
    Frontend exibe como HH:MM:SS (string).
    """
    if segundos is None or segundos < 0:
        return "00:00:00"
    
    # Garantir que é inteiro
    segundos = int(segundos)
    
    horas = segundos // 3600
    minutos = (segundos % 3600) // 60
    segs = segundos % 60
    
    # IMPLEMENTAÇÃO 7: Formato HH:MM:SS
    return f"{horas:02d}:{minutos:02d}:{segs:02d}"

def formatar_data_br(data_str):
    """Formata data para padrão brasileiro."""
    if not data_str:
        return ""
    
    try:
        # Limpar microsegundos e espaços
        data_str = str(data_str).strip()
        if '.' in data_str:
            data_str = data_str.split('.')[0]
        
        data = datetime.strptime(data_str, "%Y-%m-%d %H:%M:%S")
        return data.strftime("%d/%m/%Y %H:%M")
    except:
        return str(data_str)

def parse_datetime_safe(data_str):
    """Converte string para datetime de forma segura."""
    if not data_str:
        return None
    
    try:
        # Limpar microsegundos
        data_str = str(data_str).strip()
        if '.' in data_str:
            data_str = data_str.split('.')[0]
        
        return datetime.strptime(data_str, "%Y-%m-%d %H:%M:%S")
    except:
        return None

# ========== BADGES ==========

def badge_status(status):
    """Retorna emoji para status."""
    badges = {
        "Novo": "🔴",
        "Em atendimento": "🟡",
        "Concluído": "🟢",
        "Finalizado": "✅",
        "Cancelado": "⚫"
    }
    return badges.get(status, "⚪")

def badge_prioridade(prioridade):
    """Retorna emoji para prioridade."""
    badges = {
        "Baixa": "🟢",
        "Média": "🟡",
        "Alta": "🟠",
        "Urgente": "🔴"
    }
    return badges.get(prioridade, "⚪")

# ========== VALIDAÇÕES ==========

def validar_email(email):
    """Valida formato de email."""
    if not email:
        return False
    padrao = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(padrao, email) is not None

def validar_senha_forte(senha):
    """Valida força da senha."""
    if len(senha) < 6:
        return False, "Senha deve ter no mínimo 6 caracteres"
    return True, "Senha válida"

def sanitizar_texto(texto):
    """Remove caracteres perigosos."""
    if not texto:
        return ""
    
    # Remove tags HTML básicas
    texto = re.sub(r'<[^>]+>', '', str(texto))
    texto = ''.join(char for char in texto if ord(char) >= 32 or char in '\n\r\t')
    
    return texto.strip()

# ========== UTILITÁRIOS ==========

def registrar_log(acao, usuario, detalhes=""):
    """Registra ação do usuário."""
    pass  # Implementar se necessário

def verificar_timeout_sessao():
    """Verifica timeout de sessão."""
    pass  # Implementar se necessário
