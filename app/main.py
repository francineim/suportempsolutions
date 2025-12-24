# app/main.py
import streamlit as st
from database import criar_tabelas
from auth import login, tela_cadastro_usuario
from chamados import tela_chamados
from dashboard import tela_dashboard
from utils import verificar_timeout_sessao, registrar_log
import time

# Configuração da página
st.set_page_config(
    page_title="Helpdesk MP Solutions",
    page_icon="🎫",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS customizado
st.markdown("""
<style>
    .stApp {
        max-width: 100%;
    }
    .stButton>button {
        width: 100%;
    }
    div[data-testid="stExpander"] {
        border: 1px solid #ddd;
        border-radius: 5px;
        margin-bottom: 10px;
    }
</style>
""", unsafe_allow_html=True)


def main():
    """Função principal da aplicação."""
    
    # Criar tabelas no primeiro acesso
    criar_tabelas()
    
    # Inicializar variáveis de sessão
    if 'usuario' not in st.session_state:
        st.session_state.usuario = None
    if 'perfil' not in st.session_state:
        st.session_state.perfil = None
    if 'last_activity' not in st.session_state:
        st.session_state.last_activity = time.time()
    
    # Se já está logado
    if st.session_state.usuario:
        # Verificar timeout de sessão
        verificar_timeout_sessao()
        
        perfil = st.session_state.perfil
        usuario_logado = st.session_state.usuario
        
        # ========== SIDEBAR ==========
        st.sidebar.markdown("---")
        st.sidebar.markdown(f"### 👤 {usuario_logado}")
        
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
        
        if perfil == "admin":
            menu_opcoes["👥 Usuários"] = "usuarios"
        
        # Seleção de menu com ícones
        escolha = st.sidebar.radio(
            "**🧭 Navegação**",
            list(menu_opcoes.keys()),
            label_visibility="visible"
        )
        
        st.sidebar.markdown("---")
        
        # Informações de sessão
        with st.sidebar.expander("ℹ️ Informações da Sessão"):
            tempo_ativo = int(time.time() - st.session_state.last_activity)
            minutos_ativo = tempo_ativo // 60
            st.write(f"**Tempo inativo:** {minutos_ativo} minuto(s)")
            st.write(f"**Timeout em:** {30 - minutos_ativo} minuto(s)")
            st.caption("Sessão expira após 30 minutos de inatividade")
        
        # Botão de logout
        if st.sidebar.button("🚪 Sair", type="secondary", use_container_width=True):
            usuario_temp = st.session_state.usuario
            
            # Registrar logout
            registrar_log("LOGOUT", usuario_temp, "Logout realizado")
            
            # Limpar sessão
            st.session_state.clear()
            st.success("👋 Logout realizado com sucesso!")
            time.sleep(1)
            st.rerun()
        
        st.sidebar.markdown("---")
        st.sidebar.caption("🔒 Sistema Helpdesk v2.0")
        st.sidebar.caption("MP Solutions © 2024")
        
        # ========== CONTEÚDO PRINCIPAL ==========
        
        # Cabeçalho
        col_h1, col_h2 = st.columns([3, 1])
        with col_h1:
            st.title("🎫 Sistema Helpdesk - MP Solutions")
        with col_h2:
            st.write("")  # Espaçamento
        
        st.markdown("---")
        
        # Renderizar página selecionada
        pagina = menu_opcoes[escolha]
        
        if pagina == "chamados":
            tela_chamados(usuario_logado, perfil)
        
        elif pagina == "dashboard":
            tela_dashboard()
        
        elif pagina == "usuarios":
            tela_cadastro_usuario()
    
    else:
        # ========== TELA DE LOGIN ==========
        
        # Cabeçalho de boas-vindas
        col1, col2, col3 = st.columns([1, 2, 1])
        
        with col2:
            st.markdown("""
            <div style='text-align: center; padding: 40px 0;'>
                <h1>🎫 Sistema Helpdesk</h1>
                <h3>MP Solutions</h3>
                <p style='color: #666;'>Gestão Inteligente de Chamados</p>
            </div>
            """, unsafe_allow_html=True)
            
            st.markdown("---")
            
            # Card informativo
            st.info("""
            **👋 Bem-vindo ao Sistema Helpdesk!**
            
            Sistema completo de gerenciamento de chamados de suporte técnico.
            
            **✨ Funcionalidades:**
            - 📋 Abertura e acompanhamento de chamados
            - ⏱️ Controle de tempo de atendimento
            - 📊 Dashboard com estatísticas
            - 📎 Upload de anexos
            - 👥 Gerenciamento de usuários (admin)
            
            **🔐 Credenciais Padrão:**
            - **Usuário:** admin
            - **Senha:** sucodepao
            """)
        
        # Tentar login
        usuario_logado = login()
        
        # Se login bem-sucedido, recarregar
        if usuario_logado:
            st.rerun()
        
        # Rodapé
        st.markdown("---")
        st.markdown("""
        <div style='text-align: center; color: #666; padding: 20px 0;'>
            <p>🔒 Todos os dados são criptografados e protegidos</p>
            <p>MP Solutions © 2024 - Todos os direitos reservados</p>
        </div>
        """, unsafe_allow_html=True)


if __name__ == "__main__":
    main()
