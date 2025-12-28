# app/email_system/__init__.py
"""
Módulo de E-mail do Sistema Helpdesk
"""

from .email_service import enviar_email
from .email_templates import (
    template_base,
    email_novo_chamado_admin,
    email_novo_chamado_cliente,
    email_chamado_concluido,
    email_chamado_retornado_admin,
    email_chamado_retornado_cliente,
    email_interacao_cliente,
    email_interacao_admin,
    email_chamado_finalizado,
    email_retorno_admin_cliente
)

__all__ = [
    'enviar_email',
    'template_base',
    'email_novo_chamado_admin',
    'email_novo_chamado_cliente',
    'email_chamado_concluido',
    'email_chamado_retornado_admin',
    'email_chamado_retornado_cliente',
    'email_interacao_cliente',
    'email_interacao_admin',
    'email_chamado_finalizado',
    'email_retorno_admin_cliente'
]
