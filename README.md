# Sistema Helpdesk - MP Solutions

Sistema de gerenciamento de chamados com notificações por e-mail.

## Configuração para Streamlit Cloud

### 1. Variáveis de Ambiente/Secrets

No Streamlit Cloud, configure os seguintes secrets em `.streamlit/secrets.toml`:

```toml
# Configurações de E-mail
SMTP_HOST = "smtp.office365.com"
SMTP_PORT = "587"
SMTP_USER = "seu-email@dominio.com"
SMTP_PASSWORD = "sua-senha"
SMTP_USE_TLS = "true"

EMAIL_FROM = "Seu Nome <seu-email@dominio.com>"
EMAIL_FROM_NAME = "Help Desk"
EMAIL_FROM_ADDRESS = "seu-email@dominio.com"
EMAIL_ADMIN = "admin@dominio.com"

# Configurações do sistema
EMAIL_ENABLED = "true"
BASE_URL = "https://seusite.streamlit.app"
