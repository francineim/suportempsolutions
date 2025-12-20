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
    criar_tabelas()

    usuario_logado = login()

    if usuario_logado:
        perfil = st.session_state.perfil

        menu = ["Chamados", "Dashboard"]

        if perfil == "admin":
            menu.append("Usuários")

        escolha = st.sidebar.selectbox("Menu", menu)

        if escolha == "Chamados":
            tela_chamados(usuario_logado)

        elif escolha == "Dashboard":
            tela_dashboard()

        elif escolha == "Usuários":
            tela_cadastro_usuario()

if __name__ == "__main__":
    main()
