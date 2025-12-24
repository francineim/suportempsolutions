import streamlit as st

st.title("🎫 Sistema Helpdesk - MP Solutions")

try:
    from database import criar_tabelas
    from auth import login, tela_cadastro_usuario
    from chamados import tela_chamados
    from dashboard import tela_dashboard
    
    criar_tabelas()
    
    if 'usuario' not in st.session_state:
        st.session_state.usuario = None
    if 'perfil' not in st.session_state:
        st.session_state.perfil = None
    
    if st.session_state.usuario:
        perfil = st.session_state.perfil
        usuario_logado = st.session_state.usuario
        
        st.sidebar.markdown(f"### 👤 {usuario_logado} ({perfil})")
        st.sidebar.markdown("---")
        
        menu = ["📋 Chamados", "📊 Dashboard"]
        if perfil == "admin":
            menu.append("👥 Usuários")
        
        escolha = st.sidebar.selectbox("Menu", menu)
        
        if st.sidebar.button("🚪 Sair"):
            st.session_state.clear()
            st.rerun()
        
        if escolha == "📋 Chamados":
            tela_chamados(usuario_logado, perfil)
        elif escolha == "📊 Dashboard":
            tela_dashboard()
        elif escolha == "👥 Usuários":
            tela_cadastro_usuario()
    else:
        st.info("🔐 Login: admin / sucodepao")
        usuario_logado = login()
        if usuario_logado:
            st.rerun()

except Exception as e:
    st.error(f"❌ Erro: {str(e)}")
    import traceback
    st.code(traceback.format_exc())
