import hashlib
import secrets
import os
from datetime import datetime

def hash_senha(senha, salt=None):
    if not salt:
        salt = secrets.token_hex(16)
    hash_obj = hashlib.pbkdf2_hmac('sha256', senha.encode('utf-8'), salt.encode('utf-8'), 100000)
    return hash_obj.hex(), salt

def verificar_senha(senha, hash_armazenado, salt):
    hash_calculado, _ = hash_senha(senha, salt)
    return hash_calculado == hash_armazenado

def formatar_tempo(segundos):
    if segundos is None:
        return "00:00:00"
    horas = segundos // 3600
    minutos = (segundos % 3600) // 60
    segs = segundos % 60
    return f"{int(horas):02d}:{int(minutos):02d}:{int(segs):02d}"

def validar_email(email):
    return "@" in email and "." in email

def sanitizar_texto(texto):
    if not texto:
        return ""
    return texto.strip()

def badge_status(status):
    badges = {"Novo": "🔴", "Em atendimento": "🟡", "Concluído": "🟢"}
    return badges.get(status, "⚪")

def badge_prioridade(prioridade):
    badges = {"Baixa": "🟢", "Média": "🟡", "Alta": "🟠", "Urgente": "🔴"}
    return badges.get(prioridade, "⚪")

def validar_arquivo(arquivo):
    if arquivo is None:
        return False, "Nenhum arquivo selecionado"
    arquivo.seek(0, os.SEEK_END)
    tamanho = arquivo.tell()
    arquivo.seek(0)
    if tamanho > 10 * 1024 * 1024:
        return False, "Arquivo muito grande. Máximo: 10 MB"
    return True, "OK"

def gerar_nome_arquivo_seguro(nome_original):
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return f"{timestamp}_{nome_original}"

def formatar_data_br(data_str):
    try:
        data = datetime.strptime(data_str, "%Y-%m-%d %H:%M:%S")
        return data.strftime("%d/%m/%Y %H:%M")
    except:
        return data_str

def registrar_log(acao, usuario, detalhes=""):
    pass  # Implementar depois se quiser

def verificar_timeout_sessao():
    pass  # Implementar depois se quiser

def validar_senha_forte(senha):
    if len(senha) < 6:
        return False, "Senha muito curta"
    return True, "OK"
