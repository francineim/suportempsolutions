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
    # Criar tabelas
    criar_tabelas()
    
    # Inicializar estado da sessão se não existir
    if 'usuario' not in st.session_state:
        st.session_state.usuario = None
    if 'perfil' not in st.session_state:
        st.session_state.perfil = None
    
    # Se já está logado, usar a sessão
    if st.session_state.usuario:
        usuario_logado = st.session_state.usuario
        perfil = st.session_state.perfil
    else:
        # Se não está logado, tentar fazer login
        usuario_logado = login()
        if usuario_logado:
            perfil = st.session_state.perfil
        else:
            return  # Não está logado, para aqui
    
    # Agora, se usuario_logado não for None, mostrar o sistema
    if usuario_logado:
        menu = ["Chamados", "Dashboard"]
        if perfil == "admin":
            menu.append("Usuários")
        
        escolha = st.sidebar.selectbox("Menu", menu)
        
        if escolha == "Chamados":
            tela_chamados(usuario_logado, perfil)
        
        elif escolha == "Dashboard":
            tela_dashboard()
        
        elif escolha == "Usuários":
            tela_cadastro_usuario()
        
        # Logout
        if st.sidebar.button("Logout"):
            st.session_state.usuario = None
            st.session_state.perfil = None
            st.experimental_rerun()

if __name__ == "__main__":
    main()
