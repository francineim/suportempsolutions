# app/services/__init__.py
"""
Serviços do Sistema Helpdesk
"""

from .chamados_service import (
    criar_interacao,
    notificar_novo_chamado,
    notificar_chamado_concluido,
    notificar_chamado_retornado,
    notificar_chamado_finalizado,
    notificar_retorno_admin
)

__all__ = [
    'criar_interacao',
    'notificar_novo_chamado',
    'notificar_chamado_concluido',
    'notificar_chamado_retornado',
    'notificar_chamado_finalizado',
    'notificar_retorno_admin'
]
