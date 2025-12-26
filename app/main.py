# app/main.py - VERSÃO FINAL COMPLETA
import streamlit as st
import sys
import os

# Adicionar pasta app ao path
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

# Imports com tratamento de erro
try:
    import database
    from database import criar_tabelas, conectar
    import auth
    from auth import login, tela_cadastro_usuario
    import chamados
    from chamados import tela_chamados
    import dashboard
    from dashboard import tela_dashboard
except ImportError as e:
    st.error(f"Erro ao importar módulos: {e}")
    st.stop()

import time

# Configuração da página
st.set_page_config(
    page_title="Helpdesk – MP Solutions",
    page_icon="🎫",
    layout="wide",
    initial_sidebar_state="expanded"
)

def main():
    """Função principal da aplicação."""
    
    # Criar tabelas no primeiro acesso
    criar_tabelas()
    
    # Inicializar variáveis de sessão
    if 'usuario' not in st.session_state:
        st.session_state.usuario = None
    if 'perfil' not in st.session_state:
        st.session_state.perfil = None
    
    # Se já está logado
    if st.session_state.usuario:
        perfil = st.session_state.perfil
        usuario_logado = st.session_state.usuario
        
        # IMPLEMENTAÇÃO 4: Buscar empresa do usuário
        try:
            conn = conectar()
            cursor = conn.cursor()
            cursor.execute("SELECT empresa FROM usuarios WHERE usuario = ?", (usuario_logado,))
            resultado = cursor.fetchone()
            empresa = resultado['empresa'] if resultado and resultado['empresa'] else None
            conn.close()
        except:
            empresa = None
        
        # Nome com empresa
        if empresa:
            primeiro_nome_empresa = empresa.split()[0] if empresa else ""
            nome_exibicao = f"{usuario_logado} ({primeiro_nome_empresa})"
        else:
            nome_exibicao = usuario_logado
        
        # ========== SIDEBAR ==========
        st.sidebar.markdown("---")
        st.sidebar.markdown(f"### 👤 {nome_exibicao}")
        
        # Badge de perfil
        perfil_badges = {
            "admin": "👑 Administrador",
            "suporte": "🛠️ Suporte",
            "cliente": "👤 Cliente"
        }
        st.sidebar.markdown(f"**{perfil_badges.get(perfil, perfil)}**")
        
        st.sidebar.markdown("---")
        
        # Menu baseado no perfil
        menu_opcoes = {
            "📋 Chamados": "chamados",
            "📊 Dashboard": "dashboard"
        }
        
        # IMPLEMENTAÇÃO 3: Usuários e Force Fix apenas para admin
        if perfil == "admin":
            menu_opcoes["👥 Usuários"] = "usuarios"
            menu_opcoes["🔧 Force Fix"] = "force_fix"
        
        # Seleção de menu
        escolha = st.sidebar.radio(
            "**🧭 Navegação**",
            list(menu_opcoes.keys()),
            label_visibility="visible"
        )
        
        st.sidebar.markdown("---")
        
        # Botão de logout
        if st.sidebar.button("🚪 Sair", type="secondary", use_container_width=True):
            st.session_state.clear()
            st.success("👋 Logout realizado com sucesso!")
            time.sleep(1)
            st.rerun()
        
        st.sidebar.markdown("---")
        st.sidebar.caption("🔒 Sistema Helpdesk v2.0")
        st.sidebar.caption("MP Solutions © 2024")
        
        # ========== CONTEÚDO PRINCIPAL ==========
        st.title("🎫 Helpdesk – MP Solutions")
        st.markdown("---")
        
        # Renderizar página selecionada
        pagina = menu_opcoes[escolha]
        
        if pagina == "chamados":
            tela_chamados(usuario_logado, perfil)
        elif pagina == "dashboard":
            tela_dashboard()
        elif pagina == "usuarios":
            tela_cadastro_usuario()
        elif pagina == "force_fix":
            # Importar force_fix
            try:
                sys.path.insert(0, os.path.join(current_dir, 'pages'))
                from pages.force_fix import fix_database
                fix_database()
            except Exception as e:
                st.error(f"Erro ao carregar Force Fix: {e}")
    
    else:
        # ========== TELA DE LOGIN ==========
        col1, col2, col3 = st.columns([1, 2, 1])
        
        with col2:
            st.markdown("""
            <div style='text-align: center; padding: 40px 0;'>
                <h1>🎫 Helpdesk – MP Solutions</h1>
                <p style='color: #666;'>Gestão Inteligente de Chamados</p>
            </div>
            """, unsafe_allow_html=True)
            
            st.markdown("---")
            
            # IMPLEMENTAÇÃO 2: Remover mensagem de credenciais padrão
            st.info("**👋 Bem-vindo ao Sistema Helpdesk!**")
        
        # Tentar login
        usuario_logado = login()
        
        # Se login bem-sucedido, recarregar
        if usuario_logado:
            st.rerun()


if __name__ == "__main__":
    main()
