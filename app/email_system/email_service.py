# app/email_system/email_service.py
"""
Serviço de envio de e-mails
"""

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
import time
import sys
import os

# Adicionar pasta config ao path
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, parent_dir)

from config.email_config import (
    SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASSWORD, SMTP_USE_TLS,
    EMAIL_FROM, EMAIL_FROM_NAME, EMAIL_FROM_ADDRESS,
    EMAIL_MAX_RETRIES, EMAIL_RETRY_DELAY, EMAIL_ENABLED, EMAIL_LOG_ENVIOS
)

def enviar_email(destinatario, assunto, corpo_html, arquivos=None):
    """
    Envia um e-mail.
    
    Args:
        destinatario: E-mail do destinatário
        assunto: Assunto do e-mail
        corpo_html: Corpo do e-mail em HTML
        arquivos: Lista de caminhos de arquivos para anexar (opcional)
    
    Returns:
        tuple: (sucesso: bool, mensagem: str)
    """
    
    # Verificar se envio está habilitado
    if not EMAIL_ENABLED:
        if EMAIL_LOG_ENVIOS:
            print(f"📧 [SIMULADO] E-mail para {destinatario}: {assunto}")
        return True, "E-mail simulado (EMAIL_ENABLED=False)"
    
    # Validar destinatário
    if not destinatario or '@' not in destinatario:
        return False, f"E-mail inválido: {destinatario}"
    
    tentativa = 0
    ultima_erro = None
    
    while tentativa < EMAIL_MAX_RETRIES:
        tentativa += 1
        
        try:
            # Criar mensagem
            msg = MIMEMultipart('alternative')
            msg['From'] = EMAIL_FROM
            msg['To'] = destinatario
            msg['Subject'] = assunto
            
            # Adicionar corpo HTML
            parte_html = MIMEText(corpo_html, 'html', 'utf-8')
            msg.attach(parte_html)
            
            # Adicionar anexos se fornecidos
            if arquivos:
                for arquivo_path in arquivos:
                    if os.path.exists(arquivo_path):
                        try:
                            with open(arquivo_path, 'rb') as f:
                                parte = MIMEBase('application', 'octet-stream')
                                parte.set_payload(f.read())
                            
                            encoders.encode_base64(parte)
                            nome_arquivo = os.path.basename(arquivo_path)
                            parte.add_header(
                                'Content-Disposition',
                                f'attachment; filename= {nome_arquivo}'
                            )
                            msg.attach(parte)
                        except Exception as e:
                            print(f"⚠️ Erro ao anexar arquivo {arquivo_path}: {e}")
            
            # Conectar ao servidor SMTP
            if SMTP_USE_TLS:
                servidor = smtplib.SMTP(SMTP_HOST, SMTP_PORT)
                servidor.starttls()
            else:
                servidor = smtplib.SMTP_SSL(SMTP_HOST, SMTP_PORT)
            
            # Autenticar
            servidor.login(SMTP_USER, SMTP_PASSWORD)
            
            # Enviar e-mail
            servidor.send_message(msg)
            servidor.quit()
            
            # Log de sucesso
            if EMAIL_LOG_ENVIOS:
                print(f"✅ E-mail enviado para {destinatario}: {assunto}")
            
            return True, "E-mail enviado com sucesso"
        
        except smtplib.SMTPAuthenticationError as e:
            ultima_erro = f"Erro de autenticação: {str(e)}"
            print(f"❌ {ultima_erro}")
            break  # Não tentar novamente em caso de erro de autenticação
        
        except smtplib.SMTPException as e:
            ultima_erro = f"Erro SMTP: {str(e)}"
            print(f"⚠️ Tentativa {tentativa}/{EMAIL_MAX_RETRIES} falhou: {ultima_erro}")
            
            if tentativa < EMAIL_MAX_RETRIES:
                time.sleep(EMAIL_RETRY_DELAY)
        
        except Exception as e:
            ultima_erro = f"Erro inesperado: {str(e)}"
            print(f"❌ {ultima_erro}")
            break
    
    # Se chegou aqui, todas as tentativas falharam
    mensagem_erro = f"Falha após {EMAIL_MAX_RETRIES} tentativas. Último erro: {ultima_erro}"
    print(f"❌ {mensagem_erro}")
    return False, mensagem_erro


def enviar_email_async(destinatario, assunto, corpo_html, arquivos=None):
    """
    Envia e-mail de forma assíncrona (em thread separada).
    Útil para não bloquear a interface do Streamlit.
    
    Args:
        destinatario: E-mail do destinatário
        assunto: Assunto do e-mail
        corpo_html: Corpo do e-mail em HTML
        arquivos: Lista de caminhos de arquivos para anexar (opcional)
    """
    import threading
    
    def enviar():
        enviar_email(destinatario, assunto, corpo_html, arquivos)
    
    thread = threading.Thread(target=enviar, daemon=True)
    thread.start()


def testar_configuracao_email():
    """
    Testa a configuração de e-mail enviando um e-mail de teste.
    
    Returns:
        tuple: (sucesso: bool, mensagem: str)
    """
    print("\n🔍 Testando configuração de e-mail...")
    print(f"   Servidor: {SMTP_HOST}:{SMTP_PORT}")
    print(f"   Usuário: {SMTP_USER}")
    print(f"   TLS: {SMTP_USE_TLS}")
    print(f"   Habilitado: {EMAIL_ENABLED}")
    print()
    
    if not EMAIL_ENABLED:
        return True, "E-mail desabilitado (EMAIL_ENABLED=False)"
    
    corpo_teste = """
    <html>
        <body>
            <h2>✅ Teste de Configuração</h2>
            <p>Este é um e-mail de teste do sistema Helpdesk.</p>
            <p>Se você recebeu este e-mail, a configuração está correta!</p>
            <hr>
            <p><small>Helpdesk – MP Solutions</small></p>
        </body>
    </html>
    """
    
    return enviar_email(
        EMAIL_FROM_ADDRESS,
        "Teste - Helpdesk MP Solutions",
        corpo_teste
    )


if __name__ == "__main__":
    # Script para testar configuração
    print("="*60)
    print("TESTE DE CONFIGURAÇÃO DE E-MAIL")
    print("="*60)
    
    sucesso, mensagem = testar_configuracao_email()
    
    print()
    print("="*60)
    if sucesso:
        print("✅ TESTE BEM-SUCEDIDO!")
    else:
        print("❌ TESTE FALHOU!")
    print(f"Mensagem: {mensagem}")
    print("="*60)
