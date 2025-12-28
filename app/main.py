# app/main.py
"""
Sistema Helpdesk - MP Solutions
Arquivo principal - NÃO EXPOR DIRETAMENTE
"""

import streamlit as st
import time
from PIL import Image
import os

# Imports locais
from database import criar_tabelas, conectar, atualizar_ultimo_acesso
from auth import login, tela_cadastro_usuario
from chamados import tela_chamados
from dashboard import tela_dashboard
from utils import agora_brasilia, agora_brasilia_hora

# Configuração da página
st.set_page_config(
    page_title="Helpdesk – MP Solutions",
    page_icon="🎫",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS customizado para valorizar a logo
CUSTOM_CSS = """
<style>
    /* Container da logo */
    .logo-container {
        display: flex;
        justify-content: center;
        align-items: center;
        padding: 10px;
        margin-bottom: 10px;
    }
    
    /* Logo principal com sombra e borda */
    .logo-principal {
        max-width: 100%;
        border-radius: 10px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    }
    
    /* Header com gradiente */
    .header-mp {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 20px;
        border-radius: 10px;
        margin-bottom: 20px;
        text-align: center;
        color: white;
    }
    
    /* Badge de horário */
    .badge-hora {
        background: #f0f2f6;
        padding: 5px 15px;
        border-radius: 20px;
        font-size: 14px;
        color: #333;
    }
    
    /* Footer */
    .footer-mp {
        text-align: center;
        padding: 10px;
        color: #666;
        font-size: 12px;
        border-top: 1px solid #ddd;
        margin-top: 20px;
    }
    
    /* Esconder menu de páginas do Streamlit */
    [data-testid="stSidebarNav"] {
        display: none;
    }
    
    /* Esconder header do Streamlit */
    header[data-testid="stHeader"] {
        background: transparent;
    }
    
    /* Estilo para cards */
    .metric-card {
        background: white;
        padding: 15px;
        border-radius: 10px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
</style>
"""

def carregar_logo():
    """Carrega a logo da MP Solutions de múltiplos locais possíveis."""
    caminhos_possiveis = [
        "logo_mp.jpg",
        "app/logo_mp.jpg",
        "../logo_mp.jpg",
        os.path.join(os.path.dirname(__file__), "logo_mp.jpg"),
        os.path.join(os.path.dirname(__file__), "..", "logo_mp.jpg")
    ]
    
    for caminho in caminhos_possiveis:
        try:
            if os.path.exists(caminho):
                return Image.open(caminho)
        except:
            continue
    
    return None

def exibir_header_com_logo(logo, titulo="🎫 Helpdesk – MP Solutions"):
    """Exibe header padronizado com logo em destaque."""
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col1:
        if logo:
            st.image(logo, width=180)
    
    with col2:
        st.markdown(f"""
        <div style='text-align: center;'>
            <h1 style='margin-bottom: 5px;'>{titulo}</h1>
            <p style='color: #666;'>Gestão Inteligente de Chamados</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        # Mostrar hora de Brasília
        st.markdown(f"""
        <div style='text-align: right; padding-top: 20px;'>
            <span class='badge-hora'>🕐 Brasília: {agora_brasilia_hora()}</span>
        </div>
        """, unsafe_allow_html=True)

def main():
    """Função principal da aplicação."""
    
    # Injetar CSS customizado
    st.markdown(CUSTOM_CSS, unsafe_allow_html=True)
    
    # Criar tabelas no primeiro acesso
    criar_tabelas()
    
    # Inicializar variáveis de sessão
    if 'usuario' not in st.session_state:
        st.session_state.usuario = None
    if 'perfil' not in st.session_state:
        st.session_state.perfil = None
    
    # Carregar logo
    logo = carregar_logo()
    
    # Se já está logado
    if st.session_state.usuario:
        perfil = st.session_state.perfil
        usuario_logado = st.session_state.usuario
        
        # Atualizar último acesso
        atualizar_ultimo_acesso(usuario_logado)
        
        # Buscar empresa do usuário
        try:
            conn = conectar()
            cursor = conn.cursor()
            cursor.execute("SELECT empresa FROM usuarios WHERE usuario = ?", (usuario_logado,))
            resultado = cursor.fetchone()
            empresa = resultado['empresa'] if resultado and resultado['empresa'] else None
            conn.close()
        except:
            empresa = None
        
        # Nome com empresa
        if empresa:
            primeiro_nome_empresa = empresa.split()[0] if empresa else ""
            nome_exibicao = f"{usuario_logado} ({primeiro_nome_empresa})"
        else:
            nome_exibicao = usuario_logado
        
        # ========== SIDEBAR COM LOGO EM DESTAQUE ==========
        with st.sidebar:
            # LOGO NO TOPO DA SIDEBAR - EM DESTAQUE
            if logo:
                st.image(logo, use_container_width=True)
                st.markdown("---")
            
            # Info do usuário
            st.markdown(f"### 👤 {nome_exibicao}")
            
            # Badge de perfil
            perfil_badges = {
                "admin": "👑 Administrador",
                "suporte": "🛠️ Suporte",
                "cliente": "👤 Cliente"
            }
            st.markdown(f"**{perfil_badges.get(perfil, perfil)}**")
            
            # Horário de Brasília
            st.caption(f"🕐 {agora_brasilia_hora()} (Brasília)")
            
            st.markdown("---")
            
            # Menu baseado no perfil
            menu_opcoes = {
                "📋 Chamados": "chamados",
                "📊 Dashboard": "dashboard"
            }
            
            # Usuários e Force Fix apenas para admin
            if perfil == "admin":
                menu_opcoes["👥 Usuários"] = "usuarios"
                menu_opcoes["🔧 Force Fix"] = "force_fix"
            
            # Seleção de menu
            escolha = st.radio(
                "**🧭 Navegação**",
                list(menu_opcoes.keys()),
                label_visibility="visible"
            )
            
            st.markdown("---")
            
            # Botão de logout
            if st.button("🚪 Sair", type="secondary", use_container_width=True):
                st.session_state.clear()
                st.success("👋 Logout realizado com sucesso!")
                time.sleep(1)
                st.rerun()
            
            st.markdown("---")
            
            # Footer da sidebar
            st.caption("🔒 Sistema Helpdesk v2.1")
            st.caption("MP Solutions © 2024")
            if logo:
                st.image(logo, width=80)
        
        # ========== CONTEÚDO PRINCIPAL ==========
        # Header com logo
        exibir_header_com_logo(logo)
        
        st.markdown("---")
        
        # Renderizar página selecionada
        pagina = menu_opcoes[escolha]
        
        if pagina == "chamados":
            tela_chamados(usuario_logado, perfil)
        elif pagina == "dashboard":
            tela_dashboard()
        elif pagina == "usuarios":
            tela_cadastro_usuario()
        elif pagina == "force_fix":
            # Importar force_fix
            try:
                import sys
                sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'pages'))
                from pages.force_fix import fix_database
                fix_database()
            except Exception as e:
                st.error(f"Erro ao carregar Force Fix: {e}")
        
        # Footer
        st.markdown("---")
        st.markdown("""
        <div class='footer-mp'>
            <p>🎫 Helpdesk – MP Solutions | Todos os direitos reservados © 2024</p>
        </div>
        """, unsafe_allow_html=True)
    
    else:
        # ========== TELA DE LOGIN COM LOGO EM DESTAQUE ==========
        col1, col2, col3 = st.columns([1, 2, 1])
        
        with col2:
            # LOGO CENTRALIZADA E EM DESTAQUE NA TELA DE LOGIN
            if logo:
                st.markdown("<div class='logo-container'>", unsafe_allow_html=True)
                st.image(logo, use_container_width=True)
                st.markdown("</div>", unsafe_allow_html=True)
                st.markdown("<br>", unsafe_allow_html=True)
            
            st.markdown("""
            <div style='text-align: center; padding: 20px 0;'>
                <h1>🎫 Helpdesk – MP Solutions</h1>
                <p style='color: #666;'>Gestão Inteligente de Chamados</p>
            </div>
            """, unsafe_allow_html=True)
            
            # Horário de Brasília
            st.markdown(f"""
            <div style='text-align: center; margin-bottom: 20px;'>
                <span class='badge-hora'>🕐 Horário de Brasília: {agora_brasilia_hora()}</span>
            </div>
            """, unsafe_allow_html=True)
            
            st.markdown("---")
            
            st.info("**👋 Bem-vindo ao Sistema Helpdesk!**")
        
        # Tentar login
        usuario_logado = login()
        
        # Se login bem-sucedido, recarregar
        if usuario_logado:
            st.rerun()


if __name__ == "__main__":
    main()
