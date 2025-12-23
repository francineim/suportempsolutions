import streamlit as st
import sys
import os

# Adicionar o diretório atual ao path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database import criar_banco_se_nao_existir, verificar_estrutura
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
    
    # Sidebar - Menu de sistema
    with st.sidebar:
        st.header("⚙️ Sistema")
        
        # Botão de emergência para reset
        if st.button("🆘 Resetar Banco (Emergência)", type="secondary"):
            st.session_state.show_reset = True
        
        if st.session_state.get('show_reset', False):
            st.warning("Deseja realmente resetar o banco?")
            col1, col2 = st.columns(2)
            with col1:
                if st.button("✅ Sim, resetar"):
                    # Importar e executar reset
                    from reset_db import resetar_banco_completo
                    resetar_banco_completo()
                    st.session_state.show_reset = False
                    st.rerun()
            with col2:
                if st.button("❌ Cancelar"):
                    st.session_state.show_reset = False
                    st.rerun()
    
    # Criar banco se não existir
    criar_banco_se_nao_existir()
    
    # Verificar estrutura
    estrutura = verificar_estrutura()
    if estrutura["status"] == "error":
        st.error(f"⚠️ Problema no banco: {estrutura['message']}")
        st.info("Use o botão 'Resetar Banco' na sidebar para corrigir")
    
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
