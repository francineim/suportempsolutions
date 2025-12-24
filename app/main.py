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
    # Inicializar variáveis de sessão se não existirem
    if 'usuario' not in st.session_state:
        st.session_state.usuario = None
    if 'perfil' not in st.session_state:
        st.session_state.perfil = None
    
    # Criar tabelas (isso deve ser feito apenas uma vez, mas não faz mal se for chamado várias vezes)
    criar_tabelas()
    
    # Se o usuário já está logado, mostrar o sistema
    if st.session_state.usuario:
        perfil = st.session_state.perfil
        usuario_logado = st.session_state.usuario
        
        # Menu na sidebar
        menu = ["Chamados", "Dashboard"]
        if perfil == "admin":
            menu.append("Usuários")
        
        escolha = st.sidebar.selectbox("Menu", menu)
        
        # Exibir a tela escolhida
        if escolha == "Chamados":
            tela_chamados(usuario_logado, perfil)
        elif escolha == "Dashboard":
            tela_dashboard()
        elif escolha == "Usuários":
            tela_cadastro_usuario()
        
        # Botão de logout
        st.sidebar.markdown("---")
        if st.sidebar.button("🚪 Logout"):
            st.session_state.usuario = None
            st.session_state.perfil = None
            st.rerun()
    
    else:
        # Se não está logado, mostrar a tela de login
        usuario_logado = login()
        
        # Se o login foi bem-sucedido, atualizar a sessão e recarregar
        if usuario_logado:
            st.session_state.usuario = usuario_logado
            st.session_state.perfil = st.session_state.get('perfil', 'cliente')
            st.rerun()

if __name__ == "__main__":
    main()
