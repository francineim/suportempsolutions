# app/services/chamados_service.py
"""
Regras de negócio para chamados e integração com e-mails
"""

import sys
import os

# Adicionar pastas ao path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from database import conectar
from utils import formatar_tempo
from email.email_service import enviar_email_async
from email.email_templates import (
    email_novo_chamado_admin,
    email_novo_chamado_cliente,
    email_chamado_concluido,
    email_chamado_retornado_admin,
    email_chamado_retornado_cliente,
    email_interacao_cliente,
    email_interacao_admin
)
from config.email_config import EMAIL_ADMIN


def criar_interacao(chamado_id, autor, mensagem, tipo='resposta', enviar_email=True):
    """
    Cria uma interação no chamado e dispara e-mail se necessário.
    
    Args:
        chamado_id: ID do chamado
        autor: 'cliente' ou 'atendente'
        mensagem: Texto da mensagem
        tipo: 'abertura', 'resposta', 'conclusao', 'retorno'
        enviar_email: Se deve enviar e-mail
    
    Returns:
        tuple: (sucesso, mensagem)
    """
    try:
        conn = conectar()
        cursor = conn.cursor()
        
        # Salvar interação
        cursor.execute("""
            INSERT INTO interacoes (chamado_id, autor, mensagem, tipo, enviar_email)
            VALUES (?, ?, ?, ?, ?)
        """, (chamado_id, autor, mensagem, tipo, 1 if enviar_email else 0))
        
        interacao_id = cursor.lastrowid
        
        conn.commit()
        conn.close()
        
        # Disparar e-mail se solicitado
        if enviar_email:
            processar_envio_email_interacao(interacao_id)
        
        return True, "Interação registrada"
    
    except Exception as e:
        return False, f"Erro: {e}"


def processar_envio_email_interacao(interacao_id):
    """
    Processa envio de e-mail para uma interação.
    """
    try:
        conn = conectar()
        cursor = conn.cursor()
        
        # Buscar interação
        cursor.execute("""
            SELECT i.*, c.id as chamado_id, c.assunto, c.usuario, c.status,
                   u.email as email_cliente, u.empresa
            FROM interacoes i
            JOIN chamados c ON i.chamado_id = c.id
            JOIN usuarios u ON c.usuario = u.usuario
            WHERE i.id = ? AND i.enviar_email = 1 AND i.email_enviado = 0
        """, (interacao_id,))
        
        interacao = cursor.fetchone()
        
        if not interacao:
            conn.close()
            return
        
        interacao_dict = dict(interacao)
        
        chamado = {
            'id': interacao_dict['chamado_id'],
            'assunto': interacao_dict['assunto'],
            'usuario': interacao_dict['usuario'],
            'status': interacao_dict['status'],
            'empresa': interacao_dict.get('empresa')
        }
        
        # Decidir quem recebe o e-mail
        if interacao_dict['autor'] == 'cliente':
            # Cliente escreveu -> notificar admin
            destinatario = EMAIL_ADMIN
            corpo_html = email_interacao_admin(chamado, interacao_dict)
            assunto = f"[Chamado #{chamado['id']}] Cliente respondeu"
        else:
            # Atendente escreveu -> notificar cliente
            destinatario = interacao_dict['email_cliente']
            corpo_html = email_interacao_cliente(chamado, interacao_dict, interacao_dict['autor'])
            assunto = f"[Chamado #{chamado['id']}] Nova mensagem"
        
        # Enviar e-mail
        if destinatario:
            enviar_email_async(destinatario, assunto, corpo_html)
            
            # Marcar como enviado
            cursor.execute("""
                UPDATE interacoes SET email_enviado = 1 WHERE id = ?
            """, (interacao_id,))
            conn.commit()
        
        conn.close()
    
    except Exception as e:
        print(f"Erro ao processar e-mail de interação: {e}")


def notificar_novo_chamado(chamado_id):
    """
    Notifica admin e cliente sobre novo chamado.
    """
    try:
        conn = conectar()
        cursor = conn.cursor()
        
        # Buscar dados do chamado
        cursor.execute("""
            SELECT c.*, u.email as email_cliente, u.empresa
            FROM chamados c
            JOIN usuarios u ON c.usuario = u.usuario
            WHERE c.id = ?
        """, (chamado_id,))
        
        resultado = cursor.fetchone()
        conn.close()
        
        if not resultado:
            return
        
        chamado = dict(resultado)
        
        # E-mail para admin
        corpo_admin = email_novo_chamado_admin(chamado)
        enviar_email_async(
            EMAIL_ADMIN,
            f"[Novo Chamado #{chamado['id']}] {chamado['assunto']}",
            corpo_admin
        )
        
        # E-mail para cliente
        if chamado.get('email_cliente'):
            corpo_cliente = email_novo_chamado_cliente(chamado)
            enviar_email_async(
                chamado['email_cliente'],
                f"[Chamado #{chamado['id']}] Registrado com sucesso",
                corpo_cliente
            )
    
    except Exception as e:
        print(f"Erro ao notificar novo chamado: {e}")


def notificar_chamado_concluido(chamado_id, mensagem_conclusao=None):
    """
    Notifica cliente sobre conclusão do chamado.
    """
    try:
        conn = conectar()
        cursor = conn.cursor()
        
        # Buscar dados do chamado
        cursor.execute("""
            SELECT c.*, u.email as email_cliente
            FROM chamados c
            JOIN usuarios u ON c.usuario = u.usuario
            WHERE c.id = ?
        """, (chamado_id,))
        
        resultado = cursor.fetchone()
        conn.close()
        
        if not resultado:
            return
        
        chamado = dict(resultado)
        
        # Formatar tempo
        if chamado.get('tempo_atendimento_segundos'):
            chamado['tempo_formatado'] = formatar_tempo(chamado['tempo_atendimento_segundos'])
        
        # E-mail para cliente
        if chamado.get('email_cliente'):
            corpo = email_chamado_concluido(chamado, mensagem_conclusao)
            enviar_email_async(
                chamado['email_cliente'],
                f"[Chamado #{chamado['id']}] Concluído",
                corpo
            )
    
    except Exception as e:
        print(f"Erro ao notificar conclusão: {e}")


def notificar_chamado_retornado(chamado_id, mensagem_retorno):
    """
    Notifica admin sobre chamado retornado pelo cliente.
    """
    try:
        conn = conectar()
        cursor = conn.cursor()
        
        # Buscar dados do chamado
        cursor.execute("""
            SELECT c.*, u.email as email_cliente, u.empresa
            FROM chamados c
            JOIN usuarios u ON c.usuario = u.usuario
            WHERE c.id = ?
        """, (chamado_id,))
        
        resultado = cursor.fetchone()
        conn.close()
        
        if not resultado:
            return
        
        chamado = dict(resultado)
        
        # E-mail para admin
        corpo_admin = email_chamado_retornado_admin(chamado, mensagem_retorno)
        enviar_email_async(
            EMAIL_ADMIN,
            f"[Chamado #{chamado['id']}] Retornado pelo cliente",
            corpo_admin
        )
        
        # E-mail de confirmação para cliente
        if chamado.get('email_cliente'):
            corpo_cliente = email_chamado_retornado_cliente(chamado)
            enviar_email_async(
                chamado['email_cliente'],
                f"[Chamado #{chamado['id']}] Retornado",
                corpo_cliente
            )
    
    except Exception as e:
        print(f"Erro ao notificar retorno: {e}")
