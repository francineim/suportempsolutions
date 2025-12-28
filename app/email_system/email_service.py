# app/email_system/email_service.py
"""
Serviço de envio de e-mails
"""

import smtplib
import ssl
import time
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
import os
import sys

# Adicionar path para imports
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

from config.email_config import (
    SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASSWORD, SMTP_USE_TLS,
    EMAIL_FROM, EMAIL_FROM_ADDRESS, EMAIL_ENABLED,
    EMAIL_MAX_RETRIES, EMAIL_RETRY_DELAY,
    verificar_configuracao_email
)

def registrar_email_no_banco(destinatario, assunto, corpo, chamado_id, tipo, sucesso, erro=None):
    """Registra o e-mail no banco de dados."""
    try:
        from database import registrar_email_enviado
        registrar_email_enviado(destinatario, assunto, corpo, chamado_id, tipo, sucesso, erro)
    except Exception as e:
        print(f"⚠️ Erro ao registrar e-mail no banco: {e}")

def enviar_email(destinatario, assunto, corpo_html, anexos=None, chamado_id=None, tipo=None):
    """
    Envia e-mail via SMTP.
    """
    
    print(f"\n{'='*50}")
    print(f"📧 ENVIANDO E-MAIL")
    print(f"{'='*50}")
    print(f"   Para: {destinatario}")
    print(f"   Assunto: {assunto}")
    print(f"   Tipo: {tipo}")
    print(f"   Chamado: #{chamado_id}")
    print(f"   EMAIL_ENABLED: {EMAIL_ENABLED}")
    
    # Verificar se o e-mail está habilitado
    if not EMAIL_ENABLED:
        msg = "E-mail desabilitado (EMAIL_ENABLED=false)"
        print(f"   ⚠️ {msg}")
        registrar_email_no_banco(destinatario, assunto, corpo_html[:500] if corpo_html else "", chamado_id, tipo, True, "Simulado")
        return True, msg
    
    # Verificar configuração
    config_ok, config_msg = verificar_configuracao_email()
    if not config_ok:
        print(f"   ❌ Configuração inválida: {config_msg}")
        registrar_email_no_banco(destinatario, assunto, corpo_html[:500] if corpo_html else "", chamado_id, tipo, False, config_msg)
        return False, config_msg
    
    # Validar destinatário
    if not destinatario or '@' not in destinatario:
        msg = "Destinatário inválido"
        print(f"   ❌ {msg}")
        registrar_email_no_banco(destinatario or "N/A", assunto, corpo_html[:500] if corpo_html else "", chamado_id, tipo, False, msg)
        return False, msg
    
    # Tentar enviar com retry
    ultima_excecao = None
    
    for tentativa in range(EMAIL_MAX_RETRIES):
        try:
            print(f"   🔄 Tentativa {tentativa + 1} de {EMAIL_MAX_RETRIES}...")
            
            # Criar mensagem
            msg = MIMEMultipart('alternative')
            msg['Subject'] = assunto
            msg['From'] = EMAIL_FROM
            msg['To'] = destinatario
            
            # Adicionar corpo HTML
            parte_html = MIMEText(corpo_html, 'html', 'utf-8')
            msg.attach(parte_html)
            
            # Adicionar anexos se houver
            if anexos:
                for caminho_anexo in anexos:
                    if os.path.exists(caminho_anexo):
                        with open(caminho_anexo, 'rb') as arquivo:
                            parte = MIMEBase('application', 'octet-stream')
                            parte.set_payload(arquivo.read())
                            encoders.encode_base64(parte)
                            nome_arquivo = os.path.basename(caminho_anexo)
                            parte.add_header('Content-Disposition', f'attachment; filename="{nome_arquivo}"')
                            msg.attach(parte)
            
            # Conectar e enviar
            print(f"   📡 Conectando a {SMTP_HOST}:{SMTP_PORT}...")
            
            if SMTP_USE_TLS:
                servidor = smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=30)
                servidor.ehlo()
                servidor.starttls()
                servidor.ehlo()
            else:
                contexto = ssl.create_default_context()
                servidor = smtplib.SMTP_SSL(SMTP_HOST, SMTP_PORT, context=contexto, timeout=30)
            
            print(f"   🔐 Autenticando como {SMTP_USER}...")
            servidor.login(SMTP_USER, SMTP_PASSWORD)
            
            print(f"   📤 Enviando e-mail...")
            servidor.sendmail(EMAIL_FROM_ADDRESS, destinatario, msg.as_string())
            servidor.quit()
            
            print(f"   ✅ E-MAIL ENVIADO COM SUCESSO!")
            print(f"{'='*50}\n")
            
            registrar_email_no_banco(destinatario, assunto, corpo_html[:500] if corpo_html else "", chamado_id, tipo, True)
            
            return True, "E-mail enviado com sucesso!"
            
        except smtplib.SMTPAuthenticationError as e:
            ultima_excecao = e
            msg = f"Erro de autenticação SMTP: {e}"
            print(f"   ❌ {msg}")
            registrar_email_no_banco(destinatario, assunto, corpo_html[:500] if corpo_html else "", chamado_id, tipo, False, msg)
            return False, msg
            
        except smtplib.SMTPRecipientsRefused as e:
            ultima_excecao = e
            msg = f"Destinatário recusado: {e}"
            print(f"   ❌ {msg}")
            registrar_email_no_banco(destinatario, assunto, corpo_html[:500] if corpo_html else "", chamado_id, tipo, False, msg)
            return False, msg
            
        except smtplib.SMTPException as e:
            ultima_excecao = e
            print(f"   ⚠️ Erro SMTP (tentativa {tentativa + 1}): {e}")
            if tentativa < EMAIL_MAX_RETRIES - 1:
                print(f"   ⏳ Aguardando {EMAIL_RETRY_DELAY}s...")
                time.sleep(EMAIL_RETRY_DELAY)
                
        except Exception as e:
            ultima_excecao = e
            print(f"   ⚠️ Erro geral (tentativa {tentativa + 1}): {e}")
            if tentativa < EMAIL_MAX_RETRIES - 1:
                print(f"   ⏳ Aguardando {EMAIL_RETRY_DELAY}s...")
                time.sleep(EMAIL_RETRY_DELAY)
    
    msg = f"Falha após {EMAIL_MAX_RETRIES} tentativas: {ultima_excecao}"
    print(f"   ❌ {msg}")
    print(f"{'='*50}\n")
    
    registrar_email_no_banco(destinatario, assunto, corpo_html[:500] if corpo_html else "", chamado_id, tipo, False, str(ultima_excecao))
    
    return False, msg


def enviar_email_teste(destinatario):
    """Envia e-mail de teste."""
    corpo = """
    <!DOCTYPE html>
    <html>
    <head><meta charset="utf-8"></head>
    <body style="font-family: Arial, sans-serif; padding: 20px;">
        <div style="background: #667eea; color: white; padding: 20px; text-align: center; border-radius: 10px;">
            <h1>✅ Teste de E-mail</h1>
        </div>
        <div style="padding: 20px;">
            <p>Este é um e-mail de teste do Sistema Helpdesk MP Solutions.</p>
            <p>Se você recebeu este e-mail, a configuração está correta!</p>
            <hr>
            <p><small>Helpdesk – MP Solutions</small></p>
        </div>
    </body>
    </html>
    """
    
    return enviar_email(destinatario, "✅ Teste - Helpdesk MP Solutions", corpo, tipo="teste")
