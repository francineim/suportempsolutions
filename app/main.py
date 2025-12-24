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

# DEBUG: Verificar se estamos recarregando
if 'debug_counter' not in st.session_state:
    st.session_state.debug_counter = 0
st.session_state.debug_counter += 1

def main():
    # Mostrar debug info
    st.sidebar.write(f"🔄 Recarga #{st.session_state.debug_counter}")
    st.sidebar.write(f"📊 Sessão: usuario={st.session_state.get('usuario', 'NONE')}")
    st.sidebar.write(f"📊 Sessão: perfil={st.session_state.get('perfil', 'NONE')}")
    
    # Criar tabelas
    criar_tabelas()
    
    # Se já tem usuário na sessão, usar ele
    if st.session_state.get('usuario'):
        perfil = st.session_state.perfil
        usuario_logado = st.session_state.usuario
        
        st.sidebar.success(f"✅ Sessão ativa: {usuario_logado}")
        
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
        
        # Botão de logout
        if st.sidebar.button("Logout"):
            for key in list(st.session_state.keys()):
                del st.session_state[key]
    
    else:
        # Tentar login
        st.sidebar.warning("⚠️ Nenhuma sessão ativa")
        usuario_logado = login()
        
        # Se login OK, salvar na sessão
        if usuario_logado:
            st.session_state.usuario = usuario_logado
            st.session_state.perfil = st.session_state.get('perfil', 'cliente')
            st.experimental_rerun()

if __name__ == "__main__":
    main()
