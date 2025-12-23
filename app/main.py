import streamlit as st
from database import verificar_banco
from auth import login, tela_cadastro_usuario
from chamados import tela_chamados
from dashboard import tela_dashboard

st.set_page_config(
    page_title="Helpdesk MP Solutions",
    layout="wide",
    initial_sidebar_state="expanded"
)

def main():
    # Título principal
    st.title("🔧 Helpdesk MP Solutions")
    
    # Inicializar estado da sessão
    if 'usuario' not in st.session_state:
        st.session_state.usuario = None
    if 'perfil' not in st.session_state:
        st.session_state.perfil = None
    
    # Verificar banco
    status = verificar_banco()
    
    # Se banco tem problemas, mostrar alerta
    if status["status"] == "error":
        st.error("""
        ⚠️ **Problema no banco de dados!**
        
        A estrutura do banco está incorreta. Clique no botão abaixo para corrigir automaticamente.
        """)
        
        if st.button("🔧 Corrigir Banco de Dados Automaticamente", type="primary"):
            # Redirecionar para página de correção
            st.switch_page("app/force_fix.py")
    
    # Se já está logado
    if st.session_state.usuario:
        st.sidebar.success(f"👋 Olá, {st.session_state.usuario}!")
        
        menu = ["Chamados", "Dashboard"]
        if st.session_state.perfil == "admin":
            menu.append("Usuários")

        escolha = st.sidebar.selectbox("📋 Menu", menu)
        
        if escolha == "Chamados":
            tela_chamados(st.session_state.usuario)
        elif escolha == "Dashboard":
            tela_dashboard()
        elif escolha == "Usuários":
            tela_cadastro_usuario()
        
        # Botão de logout
        if st.sidebar.button("🚪 Logout"):
            st.session_state.usuario = None
            st.session_state.perfil = None
            st.rerun()
            
    else:
        # Tela de login
        usuario_logado = login()
        
        if usuario_logado:
            st.rerun()

if __name__ == "__main__":
    main()
