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
    # Título principal
    st.title("🔧 Helpdesk MP Solutions")
    
    # Criar tabelas e usuário admin se necessário
    admin_criado = criar_tabelas()
    
    # Se admin foi criado agora, mostrar mensagem
    if admin_criado:
        st.success("✅ Usuário admin padrão criado: 'admin' com senha 'sucodepao'")
    
    # Inicializar estado da sessão
    if 'usuario' not in st.session_state:
        st.session_state.usuario = None
    if 'perfil' not in st.session_state:
        st.session_state.perfil = None
    
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
        
        # Se fez login com sucesso, recarregar a página
        if usuario_logado:
            st.rerun()

if __name__ == "__main__":
    main()
