# app/services/chamados_service.py
"""
Serviço de Chamados - Gerencia notificações e interações
"""

import sys
import os
import threading

# Adicionar paths
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

from database import (
    conectar, 
    registrar_log,
    adicionar_interacao_chamado
)
from config.email_config import EMAIL_ADMIN, EMAIL_ENABLED
from email_system.email_service import enviar_email
from email_system.email_templates import (
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
from utils import formatar_tempo, agora_brasilia_str

def enviar_email_async(destinatario, assunto, corpo_html, chamado_id=None, tipo=None):
    """
    Envia e-mail de forma assíncrona (em thread separada).
    Útil para não bloquear a interface do Streamlit.
    """
    def enviar():
        enviar_email(destinatario, assunto, corpo_html, chamado_id=chamado_id, tipo=tipo)
    
    thread = threading.Thread(target=enviar, daemon=True)
    thread.start()

def criar_interacao(chamado_id, autor, mensagem, tipo='mensagem', enviar_email_flag=True):
    """
    Cria uma interação no chamado.
    
    Args:
        chamado_id: ID do chamado
        autor: 'cliente' ou 'atendente'
        mensagem: Texto da mensagem
        tipo: Tipo da interação (abertura, mensagem, retorno, conclusao)
        enviar_email_flag: Se deve disparar e-mail
    """
    try:
        sucesso, resultado = adicionar_interacao_chamado(chamado_id, autor, mensagem, tipo)
        
        if sucesso and enviar_email_flag:
            # Processar envio de e-mail em background
            processar_envio_email_interacao(resultado, chamado_id, autor, mensagem, tipo)
        
        return sucesso, resultado
    except Exception as e:
        print(f"Erro ao criar interação: {e}")
        return False, str(e)

def processar_envio_email_interacao(interacao_id, chamado_id, autor, mensagem, tipo):
    """
    Processa envio de e-mail para uma interação.
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
        interacao = {
            'id': interacao_id,
            'mensagem': mensagem,
            'data': agora_brasilia_str()
        }
        
        # Decidir quem recebe o e-mail
        if autor == 'cliente':
            # Cliente escreveu -> notificar admin
            if EMAIL_ADMIN:
                corpo_html = email_interacao_admin(chamado, interacao)
                enviar_email_async(
                    EMAIL_ADMIN,
                    f"[Chamado #{chamado_id}] Cliente respondeu",
                    corpo_html,
                    chamado_id=chamado_id,
                    tipo='interacao_cliente'
                )
        else:
            # Atendente escreveu -> notificar cliente
            if chamado.get('email_cliente'):
                corpo_html = email_interacao_cliente(chamado, interacao, autor)
                enviar_email_async(
                    chamado['email_cliente'],
                    f"[Chamado #{chamado_id}] Nova mensagem",
                    corpo_html,
                    chamado_id=chamado_id,
                    tipo='interacao_atendente'
                )
    
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
            print(f"⚠️ Chamado #{chamado_id} não encontrado")
            return
        
        chamado = dict(resultado)
        
        print(f"📧 Notificando sobre chamado #{chamado_id}")
        print(f"   Admin: {EMAIL_ADMIN}")
        print(f"   Cliente: {chamado.get('email_cliente', 'N/A')}")
        
        # E-mail para admin
        if EMAIL_ADMIN:
            corpo_admin = email_novo_chamado_admin(chamado)
            enviar_email_async(
                EMAIL_ADMIN,
                f"[Novo Chamado #{chamado['id']}] {chamado['assunto']}",
                corpo_admin,
                chamado_id=chamado_id,
                tipo='novo_chamado_admin'
            )
        
        # E-mail para cliente
        if chamado.get('email_cliente'):
            corpo_cliente = email_novo_chamado_cliente(chamado)
            enviar_email_async(
                chamado['email_cliente'],
                f"[Chamado #{chamado['id']}] Registrado com sucesso",
                corpo_cliente,
                chamado_id=chamado_id,
                tipo='novo_chamado_cliente'
            )
    
    except Exception as e:
        print(f"❌ Erro ao notificar novo chamado: {e}")
        import traceback
        traceback.print_exc()

def notificar_chamado_concluido(chamado_id, mensagem_conclusao=None):
    """
    Notifica cliente sobre conclusão do chamado pelo admin.
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
                f"[Chamado #{chamado['id']}] Concluído - Aguardando sua confirmação",
                corpo,
                chamado_id=chamado_id,
                tipo='chamado_concluido'
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
        if EMAIL_ADMIN:
            corpo_admin = email_chamado_retornado_admin(chamado, mensagem_retorno)
            enviar_email_async(
                EMAIL_ADMIN,
                f"[Chamado #{chamado['id']}] Retornado pelo cliente",
                corpo_admin,
                chamado_id=chamado_id,
                tipo='chamado_retornado_admin'
            )
        
        # E-mail de confirmação para cliente
        if chamado.get('email_cliente'):
            corpo_cliente = email_chamado_retornado_cliente(chamado)
            enviar_email_async(
                chamado['email_cliente'],
                f"[Chamado #{chamado['id']}] Retornado com sucesso",
                corpo_cliente,
                chamado_id=chamado_id,
                tipo='chamado_retornado_cliente'
            )
    
    except Exception as e:
        print(f"Erro ao notificar retorno: {e}")

def notificar_chamado_finalizado(chamado_id):
    """
    Notifica admin quando cliente finaliza o chamado.
    """
    try:
        conn = conectar()
        cursor = conn.cursor()
        
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
        
        if chamado.get('tempo_atendimento_segundos'):
            chamado['tempo_formatado'] = formatar_tempo(chamado['tempo_atendimento_segundos'])
        
        # E-mail para admin
        if EMAIL_ADMIN:
            corpo = email_chamado_finalizado(chamado)
            enviar_email_async(
                EMAIL_ADMIN,
                f"[Chamado #{chamado['id']}] Finalizado pelo cliente ✅",
                corpo,
                chamado_id=chamado_id,
                tipo='chamado_finalizado'
            )
    
    except Exception as e:
        print(f"Erro ao notificar finalização: {e}")

def notificar_retorno_admin(chamado_id, mensagem):
    """
    Notifica cliente quando admin retorna com pergunta.
    """
    try:
        conn = conectar()
        cursor = conn.cursor()
        
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
        
        if chamado.get('email_cliente'):
            corpo = email_retorno_admin_cliente(chamado, mensagem)
            enviar_email_async(
                chamado['email_cliente'],
                f"[Chamado #{chamado['id']}] Aguardando sua resposta",
                corpo,
                chamado_id=chamado_id,
                tipo='retorno_admin'
            )
    
    except Exception as e:
        print(f"Erro ao notificar retorno admin: {e}")
