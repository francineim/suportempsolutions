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
    
    # Login
    usuario_logado = login()
    
    if usuario_logado:
        perfil = st.session_state.perfil
        
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
            st.session_state.clear()
            st.rerun()

if __name__ == "__main__":
    main()
