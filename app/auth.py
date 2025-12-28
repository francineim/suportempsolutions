# app/auth.py
"""
Módulo de Autenticação
"""

import streamlit as st
from database import (
    conectar, 
    cadastrar_usuario_completo, 
    listar_usuarios, 
    buscar_usuario_por_id,
    atualizar_usuario,
    excluir_usuario,
    registrar_log
)
from utils import verificar_senha, hash_senha, validar_email, validar_senha_forte

def login():
    """Tela de login."""
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        with st.form("form_login"):
            st.subheader("🔐 Acesso ao Sistema")
            
            usuario = st.text_input("👤 Usuário", placeholder="Digite seu usuário")
            senha = st.text_input("🔑 Senha", type="password", placeholder="Digite sua senha")
            
            col_btn1, col_btn2 = st.columns(2)
            
            with col_btn1:
                submit = st.form_submit_button("🚀 Entrar", type="primary", use_container_width=True)
            
            with col_btn2:
                st.form_submit_button("❓ Esqueci a senha", type="secondary", use_container_width=True, disabled=True)
        
        if submit:
            if not usuario or not senha:
                st.error("⚠️ Preencha usuário e senha")
                return None
            
            try:
                conn = conectar()
                cursor = conn.cursor()
                
                cursor.execute("""
                    SELECT id, usuario, senha_hash, salt, perfil, ativo
                    FROM usuarios
                    WHERE usuario = ?
                """, (usuario.strip(),))
                
                resultado = cursor.fetchone()
                conn.close()
                
                if resultado:
                    if resultado['ativo'] == 0:
                        st.error("❌ Usuário desativado. Entre em contato com o administrador.")
                        return None
                    
                    if verificar_senha(senha, resultado['senha_hash'], resultado['salt']):
                        st.session_state.usuario = resultado['usuario']
                        st.session_state.perfil = resultado['perfil']
                        
                        registrar_log("LOGIN", resultado['usuario'], "Login bem-sucedido")
                        
                        st.success(f"✅ Bem-vindo, {resultado['usuario']}!")
                        return resultado['usuario']
                    else:
                        st.error("❌ Usuário ou senha incorretos")
                        registrar_log("LOGIN_FALHA", usuario, "Senha incorreta")
                        return None
                else:
                    st.error("❌ Usuário ou senha incorretos")
                    registrar_log("LOGIN_FALHA", usuario, "Usuário não encontrado")
                    return None
                    
            except Exception as e:
                st.error(f"❌ Erro no login: {str(e)}")
                return None
    
    return None


def tela_cadastro_usuario():
    """Tela de gerenciamento de usuários (apenas admin)."""
    st.subheader("👥 Gerenciamento de Usuários")
    
    # Verificar se é admin
    if st.session_state.get('perfil') != 'admin':
        st.error("❌ Acesso negado. Apenas administradores podem acessar esta área.")
        return
    
    # Abas
    tab_lista, tab_novo, tab_editar = st.tabs(["📋 Lista de Usuários", "➕ Novo Usuário", "✏️ Editar Usuário"])
    
    # ========== TAB: LISTA DE USUÁRIOS ==========
    with tab_lista:
        usuarios = listar_usuarios()
        
        if usuarios:
            # Filtros
            col_f1, col_f2 = st.columns(2)
            
            with col_f1:
                filtro_perfil = st.selectbox(
                    "Filtrar por perfil",
                    ["Todos", "admin", "suporte", "cliente"],
                    key="filtro_perfil_lista"
                )
            
            with col_f2:
                filtro_status = st.selectbox(
                    "Status",
                    ["Todos", "Ativos", "Inativos"],
                    key="filtro_status_lista"
                )
            
            # Aplicar filtros
            usuarios_filtrados = usuarios
            
            if filtro_perfil != "Todos":
                usuarios_filtrados = [u for u in usuarios_filtrados if u['perfil'] == filtro_perfil]
            
            if filtro_status == "Ativos":
                usuarios_filtrados = [u for u in usuarios_filtrados if u['ativo'] == 1]
            elif filtro_status == "Inativos":
                usuarios_filtrados = [u for u in usuarios_filtrados if u['ativo'] == 0]
            
            # Exibir usuários
            st.write(f"**Total: {len(usuarios_filtrados)} usuários**")
            
            for user in usuarios_filtrados:
                status_icon = "✅" if user['ativo'] == 1 else "❌"
                perfil_icon = {"admin": "👑", "suporte": "🛠️", "cliente": "👤"}.get(user['perfil'], "👤")
                
                with st.expander(f"{status_icon} {perfil_icon} {user['usuario']} - {user.get('empresa', 'N/A')}"):
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.write(f"**ID:** {user['id']}")
                        st.write(f"**Usuário:** {user['usuario']}")
                        st.write(f"**Nome:** {user.get('nome_completo', 'N/A')}")
                        st.write(f"**Perfil:** {user['perfil']}")
                    
                    with col2:
                        st.write(f"**Email:** {user.get('email', 'N/A')}")
                        st.write(f"**Empresa:** {user.get('empresa', 'N/A')}")
                        st.write(f"**Cadastro:** {user.get('data_cadastro', 'N/A')}")
                        st.write(f"**Último acesso:** {user.get('ultimo_acesso', 'N/A')}")
                    
                    # Botões de ação
                    col_btn1, col_btn2 = st.columns(2)
                    
                    with col_btn1:
                        if user['ativo'] == 1 and user['usuario'] != 'admin':
                            if st.button(f"🚫 Desativar", key=f"desativar_{user['id']}"):
                                if excluir_usuario(user['id']):
                                    st.success("Usuário desativado!")
                                    st.rerun()
                                else:
                                    st.error("Erro ao desativar")
        else:
            st.info("📭 Nenhum usuário cadastrado")
    
    # ========== TAB: NOVO USUÁRIO ==========
    with tab_novo:
        with st.form("form_novo_usuario", clear_on_submit=True):
            st.write("**Preencha os dados do novo usuário:**")
            
            col1, col2 = st.columns(2)
            
            with col1:
                novo_usuario = st.text_input("👤 Usuário *", max_chars=50)
                nova_senha = st.text_input("🔑 Senha *", type="password")
                confirmar_senha = st.text_input("🔑 Confirmar Senha *", type="password")
            
            with col2:
                novo_perfil = st.selectbox("📋 Perfil *", ["cliente", "suporte", "admin"])
                novo_nome = st.text_input("📝 Nome Completo")
            
            novo_email = st.text_input("📧 E-mail")
            nova_empresa = st.text_input("🏢 Empresa")
            
            submitted = st.form_submit_button("✅ Cadastrar Usuário", type="primary")
            
            if submitted:
                # Validações
                erros = []
                
                if not novo_usuario:
                    erros.append("Usuário é obrigatório")
                
                if not nova_senha:
                    erros.append("Senha é obrigatória")
                elif nova_senha != confirmar_senha:
                    erros.append("Senhas não conferem")
                else:
                    valido, msg = validar_senha_forte(nova_senha)
                    if not valido:
                        erros.append(msg)
                
                if novo_email and not validar_email(novo_email):
                    erros.append("E-mail inválido")
                
                if erros:
                    for erro in erros:
                        st.error(f"⚠️ {erro}")
                else:
                    # Cadastrar
                    sucesso = cadastrar_usuario_completo(
                        novo_usuario.strip(),
                        nova_senha,
                        novo_perfil,
                        novo_nome.strip() if novo_nome else None,
                        nova_empresa.strip() if nova_empresa else None,
                        novo_email.strip() if novo_email else None
                    )
                    
                    if sucesso:
                        st.success(f"✅ Usuário '{novo_usuario}' cadastrado com sucesso!")
                        st.balloons()
                    else:
                        st.error("❌ Erro ao cadastrar. Usuário ou e-mail já existe.")
    
    # ========== TAB: EDITAR USUÁRIO ==========
    with tab_editar:
        usuarios = listar_usuarios()
        
        if usuarios:
            usuario_selecionado = st.selectbox(
                "Selecione o usuário para editar",
                [f"{u['id']} - {u['usuario']} ({u['perfil']})" for u in usuarios],
                key="select_editar_usuario"
            )
            
            if usuario_selecionado:
                user_id = int(usuario_selecionado.split(" - ")[0])
                user_data = buscar_usuario_por_id(user_id)
                
                if user_data:
                    with st.form("form_editar_usuario"):
                        st.write(f"**Editando: {user_data['usuario']}**")
                        
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            edit_nome = st.text_input(
                                "📝 Nome Completo",
                                value=user_data.get('nome_completo', '') or ''
                            )
                            edit_perfil = st.selectbox(
                                "📋 Perfil",
                                ["cliente", "suporte", "admin"],
                                index=["cliente", "suporte", "admin"].index(user_data['perfil'])
                            )
                        
                        with col2:
                            edit_email = st.text_input(
                                "📧 E-mail",
                                value=user_data.get('email', '') or ''
                            )
                            edit_empresa = st.text_input(
                                "🏢 Empresa",
                                value=user_data.get('empresa', '') or ''
                            )
                        
                        st.markdown("---")
                        st.write("**Alterar Senha (deixe em branco para manter a atual)**")
                        
                        nova_senha_edit = st.text_input("🔑 Nova Senha", type="password", key="nova_senha_edit")
                        confirmar_senha_edit = st.text_input("🔑 Confirmar Nova Senha", type="password", key="confirmar_senha_edit")
                        
                        submitted = st.form_submit_button("💾 Salvar Alterações", type="primary")
                        
                        if submitted:
                            # Validar
                            erros = []
                            
                            if edit_email and not validar_email(edit_email):
                                erros.append("E-mail inválido")
                            
                            if nova_senha_edit:
                                if nova_senha_edit != confirmar_senha_edit:
                                    erros.append("Senhas não conferem")
                                else:
                                    valido, msg = validar_senha_forte(nova_senha_edit)
                                    if not valido:
                                        erros.append(msg)
                            
                            if erros:
                                for erro in erros:
                                    st.error(f"⚠️ {erro}")
                            else:
                                # Atualizar dados
                                dados = {
                                    'nome_completo': edit_nome.strip() if edit_nome else None,
                                    'email': edit_email.strip() if edit_email else None,
                                    'empresa': edit_empresa.strip() if edit_empresa else None,
                                    'perfil': edit_perfil
                                }
                                
                                sucesso = atualizar_usuario(user_id, dados)
                                
                                # Atualizar senha se fornecida
                                if nova_senha_edit and sucesso:
                                    try:
                                        senha_hash, salt = hash_senha(nova_senha_edit)
                                        conn = conectar()
                                        cursor = conn.cursor()
                                        cursor.execute("""
                                            UPDATE usuarios
                                            SET senha_hash = ?, salt = ?
                                            WHERE id = ?
                                        """, (senha_hash, salt, user_id))
                                        conn.commit()
                                        conn.close()
                                    except:
                                        pass
                                
                                if sucesso:
                                    st.success("✅ Usuário atualizado com sucesso!")
                                else:
                                    st.error("❌ Erro ao atualizar usuário")
        else:
            st.info("📭 Nenhum usuário para editar")
