# app/config/email_config.py
"""
Configurações de e-mail do sistema
IMPORTANTE: Configure via Streamlit Secrets ou variáveis de ambiente
"""

import os
import streamlit as st

def get_config_value(key, default_value=None):
    """
    Obtém valor de configuração na seguinte ordem:
    1. Streamlit secrets
    2. Variável de ambiente
    3. Valor padrão
    """
    try:
        # Tentar obter do secrets do Streamlit
        if hasattr(st, 'secrets') and key in st.secrets:
            return st.secrets[key]
    except Exception as e:
        # Ignorar erros de secrets não configurados
        pass
    
    # Tentar obter da variável de ambiente
    env_value = os.environ.get(key)
    if env_value is not None:
        return env_value
    
    # Usar valor padrão
    return default_value

# ========== CONFIGURAÇÕES DO SERVIDOR SMTP ==========
SMTP_HOST = get_config_value("SMTP_HOST", "smtp.office365.com")
SMTP_PORT = int(get_config_value("SMTP_PORT", "587"))
SMTP_USER = get_config_value("SMTP_USER", "")  # Configurar via secrets
SMTP_PASSWORD = get_config_value("SMTP_PASSWORD", "")  # Configurar via secrets
SMTP_USE_TLS = str(get_config_value("SMTP_USE_TLS", "true")).lower() == "true"

# ========== REMETENTE DOS E-MAILS ==========
EMAIL_FROM = get_config_value("EMAIL_FROM", "Help Desk <helpdesk@mpsolutions.com.br>")
EMAIL_FROM_NAME = get_config_value("EMAIL_FROM_NAME", "Help Desk MP Solutions")
EMAIL_FROM_ADDRESS = get_config_value("EMAIL_FROM_ADDRESS", "")  # Configurar via secrets

# ========== E-MAIL DO ADMIN ==========
EMAIL_ADMIN = get_config_value("EMAIL_ADMIN", "")  # Configurar via secrets

# ========== CONFIGURAÇÕES DE RETRY ==========
EMAIL_MAX_RETRIES = int(get_config_value("EMAIL_MAX_RETRIES", "3"))
EMAIL_RETRY_DELAY = int(get_config_value("EMAIL_RETRY_DELAY", "5"))

# ========== HABILITAR/DESABILITAR ENVIO ==========
# IMPORTANTE: Defina como "true" em produção quando configurar o SMTP
EMAIL_ENABLED = str(get_config_value("EMAIL_ENABLED", "false")).lower() == "true"

# ========== LOGGING ==========
EMAIL_LOG_ENVIOS = str(get_config_value("EMAIL_LOG_ENVIOS", "true")).lower() == "true"

# ========== URL BASE DO SISTEMA ==========
BASE_URL = get_config_value("BASE_URL", "https://helpdesk-mpsolutions.streamlit.app")

def verificar_configuracao_email():
    """
    Verifica se a configuração de e-mail está completa.
    Retorna: (configurado: bool, mensagem: str)
    """
    problemas = []
    
    if not SMTP_USER:
        problemas.append("SMTP_USER não configurado")
    
    if not SMTP_PASSWORD:
        problemas.append("SMTP_PASSWORD não configurado")
    
    if not EMAIL_FROM_ADDRESS:
        problemas.append("EMAIL_FROM_ADDRESS não configurado")
    
    if not EMAIL_ADMIN:
        problemas.append("EMAIL_ADMIN não configurado")
    
    if problemas:
        return False, "Configuração incompleta: " + ", ".join(problemas)
    
    return True, "Configuração OK"

def get_email_status():
    """Retorna status completo da configuração de e-mail."""
    configurado, msg = verificar_configuracao_email()
    
    return {
        "habilitado": EMAIL_ENABLED,
        "configurado": configurado,
        "mensagem": msg,
        "smtp_host": SMTP_HOST,
        "smtp_port": SMTP_PORT,
        "smtp_user": SMTP_USER[:3] + "***" if SMTP_USER else "Não configurado",
        "email_admin": EMAIL_ADMIN[:3] + "***" if EMAIL_ADMIN else "Não configurado"
    }
