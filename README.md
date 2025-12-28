# 🎫 Sistema Helpdesk - MP Solutions

Sistema de gerenciamento de chamados com notificações por e-mail.

## 📋 Funcionalidades

- ✅ Abertura de chamados com anexos
- ✅ Controle de tempo de atendimento (cronômetro)
- ✅ Notificações por e-mail (abertura, conclusão, retorno)
- ✅ Histórico de interações
- ✅ Dashboard com estatísticas
- ✅ Gestão de usuários
- ✅ Backup e restauração do banco
- ✅ Horário de Brasília em todo o sistema

## 🚀 Instalação Rápida no GitHub Codespaces

### Passo 1: Faça backup do banco atual (se existir)

```bash
# Se você já tem dados, faça backup primeiro
cp data/database.db data/database_backup_$(date +%Y%m%d_%H%M%S).db
```

### Passo 2: Substitua os arquivos

```bash
# Na raiz do projeto, execute:

# Remover arquivos antigos do app (mantém data e uploads)
rm -rf app/*.py app/config app/email_system app/services app/pages

# Copiar novos arquivos (substitua pelo caminho correto)
# Se você baixou os arquivos para uma pasta 'update':
cp -r update/app/* app/
cp update/streamlit_app.py .
cp update/requirements.txt .
cp update/.streamlit/config.toml .streamlit/
```

### Passo 3: Instalar dependências

```bash
pip install -r requirements.txt
```

### Passo 4: Inicializar/Atualizar banco de dados

```bash
cd app && python init_db.py && cd ..
```

### Passo 5: Configurar E-mail (Opcional)

Edite `.streamlit/secrets.toml`:

```toml
SMTP_HOST = "smtp.office365.com"
SMTP_PORT = "587"
SMTP_USER = "seu-email@mpsolutions.com.br"
SMTP_PASSWORD = "sua-senha"
EMAIL_FROM_ADDRESS = "seu-email@mpsolutions.com.br"
EMAIL_ADMIN = "admin@mpsolutions.com.br"
EMAIL_ENABLED = "true"
```

### Passo 6: Executar

```bash
streamlit run streamlit_app.py
```

## 📁 Estrutura do Projeto

```
helpdesk-mpsolutions/
├── .streamlit/
│   ├── config.toml         # Configurações do Streamlit
│   └── secrets.toml        # Credenciais (NÃO COMMITAR!)
├── app/
│   ├── config/
│   │   └── email_config.py # Configurações de e-mail
│   ├── email_system/
│   │   ├── email_service.py    # Serviço de envio
│   │   └── email_templates.py  # Templates HTML
│   ├── pages/
│   │   └── force_fix.py    # Ferramenta de manutenção
│   ├── services/
│   │   └── chamados_service.py # Notificações
│   ├── auth.py             # Autenticação
│   ├── chamados.py         # Tela de chamados
│   ├── dashboard.py        # Dashboard
│   ├── database.py         # Banco de dados
│   ├── main.py             # Aplicação principal
│   ├── init_db.py          # Inicialização do banco
│   └── utils.py            # Utilitários
├── data/
│   └── database.db         # Banco SQLite
├── uploads/                # Arquivos anexados
├── backups/                # Backups do banco
├── logo_mp.jpg             # Logo da empresa
├── streamlit_app.py        # Entry point
├── requirements.txt        # Dependências
└── README.md
```

## 🔧 Comandos Úteis

```bash
# Executar aplicação
streamlit run streamlit_app.py

# Inicializar banco de dados
cd app && python init_db.py

# Fazer backup manual
cp data/database.db backups/database_$(date +%Y%m%d_%H%M%S).db

# Ver logs
tail -f ~/.streamlit/logs/*.log
```

## 👤 Credenciais Padrão

- **Usuário:** admin
- **Senha:** admin123

⚠️ **IMPORTANTE:** Altere a senha após o primeiro login!

## 📧 Configuração de E-mail

O sistema suporta Office 365/Outlook. Para configurar:

1. Acesse `.streamlit/secrets.toml`
2. Configure as credenciais SMTP
3. Defina `EMAIL_ENABLED = "true"`
4. Teste em **Force Fix > Teste de E-mail**

## 🔒 Segurança

- Senhas armazenadas com hash PBKDF2
- Timeout de sessão configurável
- Logs de todas as ações
- Backup automático recomendado

## 📞 Suporte

MP Solutions - Todos os direitos reservados © 2024
