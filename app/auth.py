# app/auth.py
import streamlit as st
from database import (
    conectar, 
    cadastrar_usuario_completo, 
    listar_usuarios, 
    excluir_usuario, 
    buscar_usuario_por_id, 
    atualizar_usuario
)

def login():
    """Sistema de login com senha hash."""
    st.sidebar.subheader("🔐 Login")
    
    usuario = st.sidebar.text_input("Usuário", key="login_user")
    senha = st.sidebar.text_input("Senha", type="password", key="login_pass")
    
    if st.sidebar.button("Entrar", type="primary"):
        if not usuario or not senha:
            st.sidebar.error("⚠️ Preencha usuário e senha")
            return None
        
        conn = conectar()
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                SELECT usuario, senha_hash, salt, perfil 
                FROM usuarios 
                WHERE usuario = ? AND ativo = 1
            """, (usuario,))
            
            user = cursor.fetchone()
            
            if user:
                # Verificar senha com hash (import local)
                from utils import verificar_senha
                
                if verificar_senha(senha, user["senha_hash"], user["salt"]):
                    st.session_state.usuario = user["usuario"]
                    st.session_state.perfil = user["perfil"]
                    
                    # Registrar login no log
                    try:
                        from utils import registrar_log
                        registrar_log("LOGIN", user["usuario"], "Login realizado com sucesso")
                    except:
                        pass
                    
                    st.sidebar.success(f"✅ Bem-vindo, {user['usuario']}!")
                    return user["usuario"]
                else:
                    st.sidebar.error("❌ Senha incorreta")
                    try:
                        from utils import registrar_log
                        registrar_log("LOGIN_FALHOU", usuario, "Senha incorreta")
                    except:
                        pass
            else:
                st.sidebar.error("❌ Usuário não encontrado ou inativo")
                try:
                    from utils import registrar_log
                    registrar_log("LOGIN_FALHOU", usuario, "Usuário não encontrado")
                except:
                    pass
                
        except Exception as e:
            st.sidebar.error(f"❌ Erro no login: {str(e)}")
        finally:
            conn.close()
    
    return None


def tela_cadastro_usuario():
    """Tela completa de gerenciamento de usuários."""
    st.title("👥 Gerenciamento de Usuários")
    
    # Verificar se é admin
    if st.session_state.get('perfil') != 'admin':
        st.error("⛔ Acesso negado. Apenas administradores podem acessar esta página.")
        return
    
    tab1, tab2 = st.tabs(["📝 Cadastrar Novo", "📋 Listar Usuários"])
    
    # ========== TAB 1: CADASTRAR NOVO USUÁRIO ==========
    with tab1:
        st.subheader("📝 Cadastrar Novo Usuário")
        
        with st.form("form_cadastro_usuario", clear_on_submit=True):
            col1, col2 = st.columns(2)
            
            with col1:
                usuario = st.text_input("Usuário *", help="Nome de usuário para login")
                senha = st.text_input("Senha *", type="password", help="Mínimo 8 caracteres")
                confirmar_senha = st.text_input("Confirmar Senha *", type="password")
                perfil = st.selectbox("Perfil *", ["admin", "suporte", "cliente"])
            
            with col2:
                nome_completo = st.text_input("Nome Completo *")
                empresa = st.text_input("Empresa")
                email = st.text_input("E-mail *", help="E-mail para contato")
            
            st.markdown("---")
            st.info("**ℹ️ Requisitos de senha:**\n- Mínimo 8 caracteres\n- Pelo menos 1 letra maiúscula\n- Pelo menos 1 letra minúscula\n- Pelo menos 1 número")
            st.markdown("**Campos marcados com * são obrigatórios**")
            
            submitted = st.form_submit_button("💾 Salvar Usuário", type="primary")
            
            if submitted:
                # Validações
                if not usuario or not senha or not nome_completo or not email:
                    st.error("❌ Preencha todos os campos obrigatórios (*)")
                    return
                
                if senha != confirmar_senha:
                    st.error("❌ As senhas não coincidem")
                    return
                
                # Validar força da senha (import local)
                from utils import validar_senha_forte
                senha_valida, msg_senha = validar_senha_forte(senha)
                if not senha_valida:
                    st.error(f"❌ {msg_senha}")
                    return
                
                # Validar email (import local)
                from utils import validar_email
                if not validar_email(email):
                    st.error("❌ Digite um e-mail válido")
                    return
                
                try:
                    if cadastrar_usuario_completo(usuario, senha, perfil, nome_completo, empresa, email):
                        st.success(f"✅ Usuário '{usuario}' cadastrado com sucesso!")
                        
                        # Registrar no log (import local)
                        try:
                            from utils import registrar_log
                            registrar_log(
                                "USUARIO_CADASTRADO", 
                                st.session_state.usuario, 
                                f"Cadastrou usuário: {usuario} ({perfil})"
                            )
                        except:
                            pass
                        
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
                col_c1, col_c2, col_c3, col_c4 = st.columns(4)
                col_c1.metric("Total", len(usuarios))
                col_c2.metric("Ativos", len([u for u in usuarios if u["ativo"] == 1]))
                col_c3.metric("Inativos", len([u for u in usuarios if u["ativo"] == 0]))
                
                # Contar por perfil
                admins = len([u for u in usuarios if u["perfil"] == "admin"])
                col_c4.metric("Admins", admins)
                
                # Filtros
                st.divider()
                col_f1, col_f2 = st.columns(2)
                
                with col_f1:
                    filtro_perfil = st.selectbox(
                        "Filtrar por perfil",
                        ["Todos", "admin", "suporte", "cliente"]
                    )
                
                with col_f2:
                    filtro_status = st.selectbox(
                        "Filtrar por status",
                        ["Todos", "Ativos", "Inativos"]
                    )
                
                # Aplicar filtros
                usuarios_filtrados = usuarios
                
                if filtro_perfil != "Todos":
                    usuarios_filtrados = [u for u in usuarios_filtrados if u["perfil"] == filtro_perfil]
                
                if filtro_status == "Ativos":
                    usuarios_filtrados = [u for u in usuarios_filtrados if u["ativo"] == 1]
                elif filtro_status == "Inativos":
                    usuarios_filtrados = [u for u in usuarios_filtrados if u["ativo"] == 0]
                
                # Tabela de usuários
                st.divider()
                st.write(f"**Mostrando {len(usuarios_filtrados)} usuário(s)**")
                
                for user in usuarios_filtrados:
                    status_icon = "✅" if user["ativo"] == 1 else "❌"
                    perfil_icon = {"admin": "👑", "suporte": "🛠️", "cliente": "👤"}.get(user["perfil"], "👤")
                    
                    with st.expander(f"{status_icon} {perfil_icon} {user['usuario']} - {user['nome_completo']}"):
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
                        
                        # Ações
                        st.divider()
                        col_a1, col_a2 = st.columns(2)
                        
                        with col_a1:
                            if user["ativo"] == 1 and user["usuario"] != "admin":
                                if st.button(f"🚫 Desativar", key=f"desativar_{user['id']}"):
                                    if excluir_usuario(user['id']):
                                        st.success("Usuário desativado!")
                                        try:
                                            from utils import registrar_log
                                            registrar_log(
                                                "USUARIO_DESATIVADO",
                                                st.session_state.usuario,
                                                f"Desativou usuário: {user['usuario']}"
                                            )
                                        except:
                                            pass
                                        st.rerun()
                        
                        with col_a2:
                            if user["usuario"] == "admin":
                                st.info("ℹ️ Admin padrão não pode ser desativado")
        
        except Exception as e:
            st.error(f"❌ Erro ao carregar usuários: {str(e)}")
