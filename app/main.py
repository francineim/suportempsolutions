import streamlit as st
import sqlite3
import os

st.set_page_config(
    page_title="Helpdesk MP Solutions",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Função simples para verificar se o banco existe
def verificar_banco():
    """Verifica se o banco de dados está ok."""
    try:
        # Primeiro verificar se o arquivo existe
        if not os.path.exists("database.db"):
            return {"status": "error", "message": "Arquivo database.db não encontrado"}
        
        conn = sqlite3.connect("database.db")
        cursor = conn.cursor()
        
        # Verificar se tabela usuarios existe
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='usuarios'")
        if not cursor.fetchone():
            return {"status": "error", "message": "Tabela 'usuarios' não existe"}
        
        # Verificar se tem coluna 'senha'
        cursor.execute("PRAGMA table_info(usuarios)")
        colunas = [col[1] for col in cursor.fetchall()]
        
        if 'senha' not in colunas:
            return {"status": "error", "message": f"Coluna 'senha' não encontrada. Colunas: {colunas}"}
        
        conn.close()
        return {"status": "ok"}
        
    except Exception as e:
        return {"status": "error", "message": str(e)}


def main_page():
    """Página principal do sistema."""
    # Título principal
    st.title("🔧 Helpdesk MP Solutions")
    
    # Inicializar estado da sessão
    if 'usuario' not in st.session_state:
        st.session_state.usuario = None
    if 'perfil' not in st.session_state:
        st.session_state.perfil = None
    
    # Verificar banco
    status = verificar_banco()
    
    # Se banco tem problemas
    if status["status"] == "error":
        st.error(f"""
        ⚠️ **{status['message']}**
        
        O sistema não pode iniciar porque o banco de dados não está configurado corretamente.
        """)
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("🛠️ Configurar Banco de Dados", type="primary"):
                # Redirecionar para página de correção
                st.switch_page("pages/force_fix.py")
        
        with col2:
            if st.button("🔄 Verificar Novamente", type="secondary"):
                st.rerun()
        
        st.stop()  # Parar execução aqui
    
    # IMPORTAR DEPOIS da verificação do banco (para evitar erros de importação)
    from auth import login, tela_cadastro_usuario
    from chamados import tela_chamados
    from dashboard import tela_dashboard
    
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


def main():
    """Função principal."""
    # Verificar se estamos na página de correção
    if st.query_params.get("page") == "fix":
        import force_fix
        force_fix.fix_database()
    else:
        main_page()


if __name__ == "__main__":
    main()
