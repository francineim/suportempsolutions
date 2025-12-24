import streamlit as st
from database import criar_tabelas
from auth import login, tela_cadastro_usuario
from chamados import tela_chamados
from dashboard import tela_dashboard

st.set_page_config(
    page_title="Helpdesk MP Solutions",
    layout="wide",
    initial_sidebar_state="expanded"
)

def main():
    # Criar tabelas
    criar_tabelas()
    
    # Inicializar sessão
    if 'usuario' not in st.session_state:
        st.session_state.usuario = None
    if 'perfil' not in st.session_state:
        st.session_state.perfil = None
    
    # Se já está logado
    if st.session_state.usuario:
        perfil = st.session_state.perfil
        usuario_logado = st.session_state.usuario  # ← CORREÇÃO AQUI
        
        menu = ["📋 Chamados", "📊 Dashboard"]
        if perfil == "admin":
            menu.append("👥 Gerenciar Usuários")
        
        escolha = st.sidebar.selectbox("Menu", menu)
        
        if escolha == "📋 Chamados":
            tela_chamados(usuario_logado, perfil)
        elif escolha == "📊 Dashboard":
            tela_dashboard()
        elif escolha == "👥 Gerenciar Usuários":
            tela_cadastro_usuario()
        
        # Botão de logout
        st.sidebar.markdown("---")
        if st.sidebar.button("🚪 Logout", type="secondary"):
            st.session_state.usuario = None
            st.session_state.perfil = None
            st.rerun()
    
    else:
        # Tentar login
        usuario_logado = login()
        
        # Se login bem-sucedido
        if usuario_logado:
            st.session_state.usuario = usuario_logado
            st.session_state.perfil = st.session_state.get('perfil', 'cliente')
            st.rerun()

if __name__ == "__main__":
    main()
