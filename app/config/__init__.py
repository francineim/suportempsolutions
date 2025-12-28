# app/config/__init__.py
"""
Configurações do Sistema Helpdesk
"""

from .email_config import (
    SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASSWORD, SMTP_USE_TLS,
    EMAIL_FROM, EMAIL_FROM_NAME, EMAIL_FROM_ADDRESS,
    EMAIL_ADMIN, EMAIL_MAX_RETRIES, EMAIL_RETRY_DELAY,
    EMAIL_ENABLED, EMAIL_LOG_ENVIOS, BASE_URL,
    verificar_configuracao_email, get_email_status
)

__all__ = [
    'SMTP_HOST', 'SMTP_PORT', 'SMTP_USER', 'SMTP_PASSWORD', 'SMTP_USE_TLS',
    'EMAIL_FROM', 'EMAIL_FROM_NAME', 'EMAIL_FROM_ADDRESS',
    'EMAIL_ADMIN', 'EMAIL_MAX_RETRIES', 'EMAIL_RETRY_DELAY',
    'EMAIL_ENABLED', 'EMAIL_LOG_ENVIOS', 'BASE_URL',
    'verificar_configuracao_email', 'get_email_status'
]
