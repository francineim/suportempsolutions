# app/main.py
import streamlit as st
import sys
import os

# Adicionar pasta raiz ao path
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, current_dir)
sys.path.insert(0, parent_dir)

# Imports corrigidos para funcionar no Streamlit Cloud
from database import criar_tabelas
from auth import login, tela_cadastro_usuario
from chamados import tela_chamados
from dashboard import tela_dashboard
import time

# Configuração da página
st.set_page_config(
    page_title="Helpdesk MP Solutions",
    page_icon="🎫",
    layout="wide",
    initial_sidebar_state="expanded"
)

def main():
    """Função principal da aplicação."""
    
    # Criar tabelas no primeiro acesso
    criar_tabelas()
    
    # Inicializar variáveis de sessão
    if 'usuario' not in st.session_state:
        st.session_state.usuario = None
    if 'perfil' not in st.session_state:
        st.session_state.perfil = None
    
    # Se já está logado
    if st.session_state.usuario:
        perfil = st.session_state.perfil
        usuario_logado = st.session_state.usuario
        
        # ========== SIDEBAR ==========
        st.sidebar.markdown("---")
        st.sidebar.markdown(f"### 👤 {usuario_logado}")
        
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
        
        if perfil == "admin":
            menu_opcoes["👥 Usuários"] = "usuarios"
        
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
        st.title("🎫 Sistema Helpdesk - MP Solutions")
        st.markdown("---")
        
        # Renderizar página selecionada
        pagina = menu_opcoes[escolha]
        
        if pagina == "chamados":
            tela_chamados(usuario_logado, perfil)
        elif pagina == "dashboard":
            tela_dashboard()
        elif pagina == "usuarios":
            tela_cadastro_usuario()
    
    else:
        # ========== TELA DE LOGIN ==========
        col1, col2, col3 = st.columns([1, 2, 1])
        
        with col2:
            st.markdown("""
            <div style='text-align: center; padding: 40px 0;'>
                <h1>🎫 Sistema Helpdesk</h1>
                <h3>MP Solutions</h3>
                <p style='color: #666;'>Gestão Inteligente de Chamados</p>
            </div>
            """, unsafe_allow_html=True)
            
            st.markdown("---")
            
            st.info("""
            **👋 Bem-vindo ao Sistema Helpdesk!**
            
            **🔐 Credenciais Padrão:**
            - **Usuário:** admin
            - **Senha:** sucodepao
            """)
        
        # Tentar login
        usuario_logado = login()
        
        # Se login bem-sucedido, recarregar
        if usuario_logado:
            st.rerun()


if __name__ == "__main__":
    main()
