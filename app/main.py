# app/main.py
import streamlit as st
import time
from PIL import Image

# Imports locais (dentro da pasta app/)
from database import criar_tabelas, conectar
from auth import login, tela_cadastro_usuario
from chamados import tela_chamados
from dashboard import tela_dashboard

# Configuração da página
st.set_page_config(
    page_title="Helpdesk – MP Solutions",
    page_icon="🎫",
    layout="wide",
    initial_sidebar_state="expanded"
)

def carregar_logo():
    """Carrega a logo da MP Solutions."""
    try:
        return Image.open("logo_mp.jpg")
    except:
        return None

def main():
    """Função principal da aplicação."""
    
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
        
        # ========== SIDEBAR ==========
        # LOGO NO TOPO DA SIDEBAR
        if logo:
            st.sidebar.image(logo, use_container_width=True)
            st.sidebar.markdown("---")
        
        st.sidebar.markdown(f"### 👤 {nome_exibicao}")
        
        # Badge de perfil
        perfil_badges = {
            "admin": "👑 Administrador",
            "suporte": "🛠️ Suporte",
            "cliente": "👤 Cliente"
        }
        st.sidebar.markdown(f"**{perfil_badges.get(perfil, perfil)}**")
        
        st.sidebar.markdown("---")
        
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
        escolha = st.sidebar.radio(
            "**🧭 Navegação**",
            list(menu_opcoes.keys()),
            label_visibility="visible"
        )
        
        st.sidebar.markdown("---")
        
        # Botão de logout
        if st.sidebar.button("🚪 Sair", type="secondary", use_container_width=True):
            st.session_state.clear()
            st.success("👋 Logout realizado com sucesso!")
            time.sleep(1)
            st.rerun()
        
        st.sidebar.markdown("---")
        st.sidebar.caption("🔒 Sistema Helpdesk v2.0")
        st.sidebar.caption("MP Solutions © 2024")
        
        # ========== CONTEÚDO PRINCIPAL ==========
        # LOGO NO HEADER PRINCIPAL
        col_header1, col_header2, col_header3 = st.columns([1, 2, 1])
        
        with col_header1:
            if logo:
                st.image(logo, width=200)
        
        with col_header2:
            st.title("🎫 Helpdesk – MP Solutions")
        
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
                import os
                sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'pages'))
                from pages.force_fix import fix_database
                fix_database()
            except Exception as e:
                st.error(f"Erro ao carregar Force Fix: {e}")
    
    else:
        # ========== TELA DE LOGIN ==========
        col1, col2, col3 = st.columns([1, 2, 1])
        
        with col2:
            # LOGO NA TELA DE LOGIN
            if logo:
                st.image(logo, use_container_width=True)
                st.markdown("<br>", unsafe_allow_html=True)
            
            st.markdown("""
            <div style='text-align: center; padding: 20px 0;'>
                <h1>🎫 Helpdesk – MP Solutions</h1>
                <p style='color: #666;'>Gestão Inteligente de Chamados</p>
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
