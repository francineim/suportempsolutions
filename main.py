import streamlit as st

from database import criar_tabelas
from chamados import tela_chamados
from dashboard import tela_dashboard
from auth import login

st.set_page_config(
    page_title="Helpdesk MP Solutions",
    layout="wide"
)

def main():
    criar_tabelas()

    usuario_logado = login()

    if usuario_logado:
        menu = st.sidebar.selectbox(
            "Menu",
            ["Chamados", "Dashboard"]
        )

        if menu == "Chamados":
            tela_chamados(usuario_logado)

        elif menu == "Dashboard":
            tela_dashboard()

if __name__ == "__main__":
    main()
