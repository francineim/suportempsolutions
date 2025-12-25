# app/config/email_config.py
"""
Configurações de e-mail do sistema
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
    except:
        pass
    
    # Tentar obter da variável de ambiente
    env_value = os.environ.get(key)
    if env_value is not None:
        return env_value
    
    # Usar valor padrão
    return default_value

# Configurações do servidor SMTP (Office365)
SMTP_HOST = get_config_value("SMTP_HOST", "smtp.office365.com")
SMTP_PORT = int(get_config_value("SMTP_PORT", "587"))
SMTP_USER = get_config_value("SMTP_USER", "francinei@mpsolutions.com.br")
SMTP_PASSWORD = get_config_value("SMTP_PASSWORD", "")
SMTP_USE_TLS = get_config_value("SMTP_USE_TLS", "true").lower() == "true"

# Remetente dos e-mails
EMAIL_FROM = get_config_value("EMAIL_FROM", "Francinei - Help Desk <francinei@mpsolutions.com.br>")
EMAIL_FROM_NAME = get_config_value("EMAIL_FROM_NAME", "Francinei - Help Desk")
EMAIL_FROM_ADDRESS = get_config_value("EMAIL_FROM_ADDRESS", "francinei@mpsolutions.com.br")

# E-mail do admin
EMAIL_ADMIN = get_config_value("EMAIL_ADMIN", "francinei@mpsolutions.com.br")

# Configurações de retry
EMAIL_MAX_RETRIES = int(get_config_value("EMAIL_MAX_RETRIES", "3"))
EMAIL_RETRY_DELAY = int(get_config_value("EMAIL_RETRY_DELAY", "5"))

# Habilitar/desabilitar envio de e-mails
EMAIL_ENABLED = get_config_value("EMAIL_ENABLED", "true").lower() == "true"

# Configurações de logging
EMAIL_LOG_ENVIOS = get_config_value("EMAIL_LOG_ENVIOS", "true").lower() == "true"

# URL base do sistema
BASE_URL = get_config_value("BASE_URL", "https://helpdesk-mpsolutions.streamlit.app")
