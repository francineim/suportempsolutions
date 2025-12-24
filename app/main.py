import streamlit as st
from database import criar_tabelas
from auth import login, tela_cadastro_usuario
from chamados import tela_chamados
from dashboard import tela_dashboard

st.set_page_config(
    page_title="Helpdesk MP Solutions",
    layout="wide",
    page_icon="🔧",
    initial_sidebar_state="expanded"
)

def main():
    # Criar tabelas (agora inclui tabela de anexos)
    criar_tabelas()
    
    # Login
    usuario_logado = login()
    
    if usuario_logado:
        perfil = st.session_state.perfil
        
        # Sidebar com informações do usuário
        st.sidebar.markdown(f"### 👤 {usuario_logado}")
        st.sidebar.markdown(f"**Perfil:** {perfil}")
        st.sidebar.markdown("---")
        
        menu = ["📋 Chamados", "📊 Dashboard"]
        if perfil == "admin":
            menu.append("👥 Usuários")
        
        escolha = st.sidebar.selectbox("Menu", menu)
        
        # PASSAR PERFIL PARA TELA_CHAMADOS
        if escolha == "📋 Chamados":
            tela_chamados(usuario_logado, perfil)  # ← AQUI: adicionado perfil
        
        elif escolha == "📊 Dashboard":
            tela_dashboard()
        
        elif escolha == "👥 Usuários":
            tela_cadastro_usuario()
        
        # Botão de logout
        st.sidebar.markdown("---")
        if st.sidebar.button("🚪 Logout", type="secondary"):
            st.session_state.clear()
            st.rerun()
        
        # Link para force_fix (apenas admin)
        if perfil == "admin":
            st.sidebar.markdown("---")
            st.sidebar.markdown("[🛠️ Ferramentas Admin](/force_fix)")

if __name__ == "__main__":
    main()
