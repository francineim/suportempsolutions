import streamlit as st

from database import criar_tabelas
from auth import login, tela_cadastro_usuario
from chamados import tela_chamados
from dashboard import tela_dashboard

st.set_page_config(
    page_title="Helpdesk MP Solutions",
    layout="wide"
)

def main():
    # Criar tabelas e usuário admin padrão
    criar_tabelas()
    
    # Inicializar estado da sessão
    if 'usuario' not in st.session_state:
        st.session_state.usuario = None
    if 'perfil' not in st.session_state:
        st.session_state.perfil = None
    
    # Verificar se já está logado
    if st.session_state.usuario:
        usuario_logado = st.session_state.usuario
        perfil = st.session_state.perfil
    else:
        usuario_logado = login()

    if usuario_logado:
        perfil = st.session_state.perfil

        menu = ["Chamados", "Dashboard"]

        if perfil == "admin":
            menu.append("Usuários")

        escolha = st.sidebar.selectbox("Menu", menu)
        
        # Botão de logout
        if st.sidebar.button("Logout"):
            st.session_state.usuario = None
            st.session_state.perfil = None
            st.rerun()

        if escolha == "Chamados":
            tela_chamados(usuario_logado)

        elif escolha == "Dashboard":
            tela_dashboard()

        elif escolha == "Usuários":
            tela_cadastro_usuario()

if __name__ == "__main__":
    main()
