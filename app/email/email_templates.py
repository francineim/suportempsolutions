# app/email/email_templates.py
"""
Templates HTML para e-mails do sistema
"""

def template_base(titulo, conteudo):
    """Template base para todos os e-mails."""
    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <style>
            body {{
                font-family: Arial, sans-serif;
                line-height: 1.6;
                color: #333;
                max-width: 600px;
                margin: 0 auto;
                padding: 20px;
            }}
            .header {{
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                padding: 30px;
                text-align: center;
                border-radius: 10px 10px 0 0;
            }}
            .header h1 {{
                margin: 0;
                font-size: 24px;
            }}
            .content {{
                background: #f9f9f9;
                padding: 30px;
                border: 1px solid #ddd;
                border-top: none;
            }}
            .chamado-info {{
                background: white;
                padding: 20px;
                border-radius: 8px;
                margin: 20px 0;
                border-left: 4px solid #667eea;
            }}
            .chamado-info p {{
                margin: 10px 0;
            }}
            .chamado-info strong {{
                color: #667eea;
            }}
            .mensagem-box {{
                background: white;
                padding: 15px;
                border-radius: 8px;
                margin: 15px 0;
                border: 1px solid #e0e0e0;
            }}
            .button {{
                display: inline-block;
                padding: 12px 30px;
                background: #667eea;
                color: white !important;
                text-decoration: none;
                border-radius: 5px;
                margin: 20px 0;
                font-weight: bold;
            }}
            .footer {{
                text-align: center;
                padding: 20px;
                color: #666;
                font-size: 12px;
                border-top: 1px solid #ddd;
                margin-top: 20px;
            }}
            .status {{
                display: inline-block;
                padding: 5px 15px;
                border-radius: 20px;
                font-size: 12px;
                font-weight: bold;
            }}
            .status-novo {{
                background: #ffebee;
                color: #c62828;
            }}
            .status-atendimento {{
                background: #fff3e0;
                color: #e65100;
            }}
            .status-concluido {{
                background: #e8f5e9;
                color: #2e7d32;
            }}
        </style>
    </head>
    <body>
        <div class="header">
            <h1>🎫 Helpdesk – MP Solutions</h1>
            <p>{titulo}</p>
        </div>
        <div class="content">
            {conteudo}
        </div>
        <div class="footer">
            <p>Este é um e-mail automático. Por favor, não responda.</p>
            <p>© 2024 MP Solutions - Todos os direitos reservados</p>
        </div>
    </body>
    </html>
    """

def email_novo_chamado_admin(chamado):
    """E-mail para admin quando novo chamado é aberto."""
    conteudo = f"""
        <h2>📢 Novo Chamado Aberto</h2>
        <p>Um novo chamado foi registrado no sistema e aguarda atendimento.</p>
        
        <div class="chamado-info">
            <p><strong>Chamado:</strong> #{chamado['id']}</p>
            <p><strong>Assunto:</strong> {chamado['assunto']}</p>
            <p><strong>Prioridade:</strong> <span class="status status-novo">{chamado['prioridade']}</span></p>
            <p><strong>Cliente:</strong> {chamado['usuario']}</p>
            <p><strong>Empresa:</strong> {chamado.get('empresa', 'Não informada')}</p>
            <p><strong>Data:</strong> {chamado['data_abertura']}</p>
        </div>
        
        <div class="mensagem-box">
            <strong>Descrição:</strong>
            <p>{chamado['descricao']}</p>
        </div>
        
        <p>⚠️ Acesse o sistema para iniciar o atendimento.</p>
    """
    
    return template_base("Novo Chamado Recebido", conteudo)

def email_novo_chamado_cliente(chamado):
    """E-mail de confirmação para cliente quando abre chamado."""
    conteudo = f"""
        <h2>✅ Chamado Registrado com Sucesso</h2>
        <p>Olá <strong>{chamado['usuario']}</strong>,</p>
        <p>Seu chamado foi registrado e em breve será atendido por nossa equipe.</p>
        
        <div class="chamado-info">
            <p><strong>Número do Chamado:</strong> #{chamado['id']}</p>
            <p><strong>Assunto:</strong> {chamado['assunto']}</p>
            <p><strong>Prioridade:</strong> <span class="status status-novo">{chamado['prioridade']}</span></p>
            <p><strong>Status:</strong> <span class="status status-novo">Novo</span></p>
            <p><strong>Data de Abertura:</strong> {chamado['data_abertura']}</p>
        </div>
        
        <div class="mensagem-box">
            <strong>Sua mensagem:</strong>
            <p>{chamado['descricao']}</p>
        </div>
        
        <p>📌 <strong>Guarde o número #{chamado['id']} para referências futuras.</strong></p>
        <p>Você receberá atualizações por e-mail sobre o andamento do chamado.</p>
    """
    
    return template_base("Chamado Registrado", conteudo)

def email_chamado_concluido(chamado, mensagem_conclusao):
    """E-mail para cliente quando chamado é concluído."""
    conteudo = f"""
        <h2>✅ Chamado Concluído</h2>
        <p>Olá <strong>{chamado['usuario']}</strong>,</p>
        <p>Seu chamado foi concluído por nossa equipe.</p>
        
        <div class="chamado-info">
            <p><strong>Chamado:</strong> #{chamado['id']}</p>
            <p><strong>Assunto:</strong> {chamado['assunto']}</p>
            <p><strong>Status:</strong> <span class="status status-concluido">Concluído</span></p>
            <p><strong>Atendente:</strong> {chamado.get('atendente', 'N/A')}</p>
            <p><strong>Tempo de Atendimento:</strong> {chamado.get('tempo_formatado', 'N/A')}</p>
        </div>
        
        {f'''
        <div class="mensagem-box">
            <strong>Mensagem do Atendente:</strong>
            <p>{mensagem_conclusao}</p>
        </div>
        ''' if mensagem_conclusao else ''}
        
        <p>Se o problema não foi resolvido ou você precisa de mais informações, 
        você pode <strong>retornar o chamado</strong> através do sistema.</p>
        
        <p>Caso o problema esteja resolvido, agradecemos por utilizar nossos serviços! 😊</p>
    """
    
    return template_base("Chamado Concluído", conteudo)

def email_chamado_retornado_admin(chamado, mensagem_retorno):
    """E-mail para admin quando cliente retorna chamado."""
    conteudo = f"""
        <h2>🔄 Chamado Retornado pelo Cliente</h2>
        <p>O cliente retornou um chamado que estava concluído.</p>
        
        <div class="chamado-info">
            <p><strong>Chamado:</strong> #{chamado['id']}</p>
            <p><strong>Assunto:</strong> {chamado['assunto']}</p>
            <p><strong>Cliente:</strong> {chamado['usuario']}</p>
            <p><strong>Empresa:</strong> {chamado.get('empresa', 'N/A')}</p>
            <p><strong>Status:</strong> <span class="status status-atendimento">Em Atendimento</span></p>
            <p><strong>Retornos:</strong> {chamado.get('retornos', 1)}x</p>
        </div>
        
        <div class="mensagem-box">
            <strong>Mensagem do Cliente:</strong>
            <p>{mensagem_retorno}</p>
        </div>
        
        <p>⚠️ O chamado foi reaberto e aguarda novo atendimento.</p>
    """
    
    return template_base("Chamado Retornado", conteudo)

def email_chamado_retornado_cliente(chamado):
    """E-mail de confirmação para cliente quando retorna chamado."""
    conteudo = f"""
        <h2>🔄 Chamado Retornado com Sucesso</h2>
        <p>Olá <strong>{chamado['usuario']}</strong>,</p>
        <p>Seu chamado foi reaberto e nossa equipe irá analisá-lo novamente.</p>
        
        <div class="chamado-info">
            <p><strong>Chamado:</strong> #{chamado['id']}</p>
            <p><strong>Assunto:</strong> {chamado['assunto']}</p>
            <p><strong>Status:</strong> <span class="status status-atendimento">Em Atendimento</span></p>
        </div>
        
        <p>Aguarde o contato da nossa equipe.</p>
    """
    
    return template_base("Chamado Retornado", conteudo)

def email_interacao_cliente(chamado, interacao, autor):
    """E-mail para cliente quando há nova interação do atendente."""
    autor_nome = "Atendente" if autor == "atendente" else "Cliente"
    
    conteudo = f"""
        <h2>💬 Nova Mensagem no Chamado #{chamado['id']}</h2>
        <p>Olá <strong>{chamado['usuario']}</strong>,</p>
        <p>Há uma nova mensagem no seu chamado.</p>
        
        <div class="chamado-info">
            <p><strong>Chamado:</strong> #{chamado['id']}</p>
            <p><strong>Assunto:</strong> {chamado['assunto']}</p>
            <p><strong>Status:</strong> {chamado['status']}</p>
        </div>
        
        <div class="mensagem-box">
            <strong>{autor_nome} escreveu:</strong>
            <p>{interacao['mensagem']}</p>
            <small style="color: #666;">Em: {interacao['data']}</small>
        </div>
        
        <p>Acesse o sistema para visualizar e responder.</p>
    """
    
    return template_base("Nova Mensagem no Chamado", conteudo)

def email_interacao_admin(chamado, interacao):
    """E-mail para admin quando cliente interage."""
    conteudo = f"""
        <h2>💬 Cliente Respondeu no Chamado #{chamado['id']}</h2>
        
        <div class="chamado-info">
            <p><strong>Chamado:</strong> #{chamado['id']}</p>
            <p><strong>Assunto:</strong> {chamado['assunto']}</p>
            <p><strong>Cliente:</strong> {chamado['usuario']}</p>
            <p><strong>Status:</strong> {chamado['status']}</p>
        </div>
        
        <div class="mensagem-box">
            <strong>Mensagem do cliente:</strong>
            <p>{interacao['mensagem']}</p>
        </div>
        
        <p>⚠️ Acesse o sistema para visualizar e responder.</p>
    """
    
    return template_base("Nova Resposta do Cliente", conteudo)
