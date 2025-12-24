import streamlit as st
from database import conectar, cadastrar_usuario_completo, listar_usuarios, excluir_usuario, buscar_usuario_por_id, atualizar_usuario

def login():
    st.sidebar.subheader("Login")
    
    usuario = st.sidebar.text_input("Usuário")
    senha = st.sidebar.text_input("Senha", type="password")
    
    if st.sidebar.button("Entrar"):
        if not usuario or not senha:
            st.sidebar.error("Preencha usuário e senha")
            return None
        
        conn = conectar()
        cursor = conn.cursor()
        
        try:
            cursor.execute(
                "SELECT usuario, senha, perfil FROM usuarios WHERE usuario = ? AND ativo = 1",
                (usuario,)
            )
            user = cursor.fetchone()
            
            if user:
                if senha == user["senha"]:
                    st.session_state.usuario = user["usuario"]
                    st.session_state.perfil = user["perfil"]
                    st.sidebar.success(f"Bem-vindo, {user['usuario']}")
                    return user["usuario"]
                else:
                    st.sidebar.error("Senha incorreta")
            else:
                st.sidebar.error("Usuário não encontrado ou inativo")
                
        except Exception as e:
            st.sidebar.error(f"Erro no login: {str(e)}")
        finally:
            conn.close()
    
    return None

def tela_cadastro_usuario():
    """Tela completa de gerenciamento de usuários."""
    st.title("👥 Gerenciamento de Usuários")
    
    tab1, tab2 = st.tabs(["📝 Cadastrar Novo", "📋 Listar Usuários"])
    
    # ========== TAB 1: CADASTRAR NOVO USUÁRIO ==========
    with tab1:
        st.subheader("📝 Cadastrar Novo Usuário")
        
        with st.form("form_cadastro_usuario", clear_on_submit=True):
            col1, col2 = st.columns(2)
            
            with col1:
                usuario = st.text_input("Usuário *", help="Nome de usuário para login")
                senha = st.text_input("Senha *", type="password")
                confirmar_senha = st.text_input("Confirmar Senha *", type="password")
                perfil = st.selectbox("Perfil *", ["admin", "suporte", "cliente"])
            
            with col2:
                nome_completo = st.text_input("Nome Completo *")
                empresa = st.text_input("Empresa")
                email = st.text_input("E-mail *", help="E-mail para contato")
            
            st.markdown("**Campos marcados com * são obrigatórios**")
            
            submitted = st.form_submit_button("💾 Salvar Usuário", type="primary")
            
            if submitted:
                # Validações
                if not usuario or not senha or not nome_completo or not email:
                    st.error("Preencha todos os campos obrigatórios (*)")
                    return
                
                if senha != confirmar_senha:
                    st.error("As senhas não coincidem")
                    return
                
                if "@" not in email or "." not in email:
                    st.error("Digite um e-mail válido")
                    return
                
                try:
                    if cadastrar_usuario_completo(usuario, senha, perfil, nome_completo, empresa, email):
                        st.success(f"✅ Usuário '{usuario}' cadastrado com sucesso!")
                        st.balloons()
                    else:
                        st.error("❌ Erro ao cadastrar usuário. Verifique se o usuário ou e-mail já existem.")
                except Exception as e:
                    st.error(f"❌ Erro: {str(e)}")
    
    # ========== TAB 2: LISTAR USUÁRIOS ==========
    with tab2:
        st.subheader("📋 Usuários Cadastrados")
        
        try:
            usuarios = listar_usuarios()
            
            if not usuarios:
                st.info("📭 Nenhum usuário cadastrado")
            else:
                # Mostrar contadores
                col_c1, col_c2, col_c3 = st.columns(3)
                col_c1.metric("Total", len(usuarios))
                col_c2.metric("Ativos", len([u for u in usuarios if u["ativo"] == 1]))
                col_c3.metric("Inativos", len([u for u in usuarios if u["ativo"] == 0]))
                
                # Tabela de usuários
                st.divider()
                
                for user in usuarios:
                    with st.expander(f"👤 {user['usuario']} - {user['nome_completo']}"):
                        col_u1, col_u2 = st.columns(2)
                        
                        with col_u1:
                            st.write(f"**ID:** {user['id']}")
                            st.write(f"**Usuário:** {user['usuario']}")
                            st.write(f"**Perfil:** {user['perfil']}")
                            st.write(f"**Status:** {'✅ Ativo' if user['ativo'] == 1 else '❌ Inativo'}")
                        
                        with col_u2:
                            st.write(f"**Nome:** {user['nome_completo']}")
                            st.write(f"**Empresa:** {user['empresa'] or 'Não informada'}")
                            st.write(f"**E-mail:** {user['email']}")
                            st.write(f"**Cadastro:** {user['data_cadastro']}")
        
        except Exception as e:
            st.error(f"❌ Erro ao carregar usuários: {str(e)}")
