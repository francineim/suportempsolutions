import streamlit as st
from database import conectar


def login():
    st.sidebar.subheader("Login")

    usuario = st.sidebar.text_input("Usuário")
    senha = st.sidebar.text_input("Senha", type="password")

    if st.sidebar.button("Entrar"):
        # DEBUG: Mostrar o que está sendo digitado
        st.sidebar.write(f"Tentando login com: usuário='{usuario}', senha='{senha}'")
        
        if not usuario or not senha:
            st.sidebar.error("Por favor, preencha todos os campos")
            return None
        
        conn = conectar()
        cursor = conn.cursor()

        # DEBUG: Listar todos os usuários antes da busca
        cursor.execute("SELECT usuario, senha, perfil FROM usuarios")
        todos_usuarios = cursor.fetchall()
        st.sidebar.write(f"DEBUG - Todos usuários no BD: {[u['usuario'] for u in todos_usuarios]}")
        
        # Buscar usuário específico
        cursor.execute(
            "SELECT usuario, senha, perfil FROM usuarios WHERE usuario = ?",
            (usuario,)
        )
        user = cursor.fetchone()
        conn.close()

        if user:
            st.sidebar.write(f"DEBUG - Usuário encontrado: {user['usuario']}")
            st.sidebar.write(f"DEBUG - Senha no BD: '{user['senha']}'")
            st.sidebar.write(f"DEBUG - Senha digitada: '{senha}'")
            
            # Comparação simples (sem bcrypt por enquanto)
            if senha == user["senha"]:
                st.session_state.usuario = user["usuario"]
                st.session_state.perfil = user["perfil"]
                st.sidebar.success(f"✅ Login bem-sucedido! Bem-vindo, {user['usuario']}")
                return user["usuario"]
            else:
                st.sidebar.error("❌ Senha incorreta")
        else:
            st.sidebar.error("❌ Usuário não encontrado no banco de dados")

    return None


def tela_cadastro_usuario():
    st.subheader("Cadastro de Usuários")

    usuario = st.text_input("Usuário")
    senha = st.text_input("Senha", type="password")
    perfil = st.selectbox("Perfil", ["admin", "cliente", "suporte"])

    if st.button("Cadastrar usuário"):
        if not usuario or not senha:
            st.error("Por favor, preencha todos os campos")
            return
            
        conn = conectar()
        cursor = conn.cursor()

        try:
            cursor.execute(
                "INSERT INTO usuarios (usuario, senha, perfil) VALUES (?, ?, ?)",
                (usuario, senha, perfil)
            )
            conn.commit()
            st.success(f"✅ Usuário '{usuario}' cadastrado com sucesso!")
            
            # Mostrar todos os usuários após cadastro
            cursor.execute("SELECT usuario, perfil FROM usuarios")
            usuarios = cursor.fetchall()
            st.write(f"📋 Usuários no sistema: {[u['usuario'] for u in usuarios]}")
            
        except Exception as e:
            if "UNIQUE constraint failed" in str(e):
                st.error("❌ Usuário já existe")
            else:
                st.error(f"❌ Erro ao cadastrar: {str(e)}")
        finally:
            conn.close()
