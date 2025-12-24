import streamlit as st
from database import conectar


def login():
    st.sidebar.subheader("Login")

    usuario = st.sidebar.text_input("Usuário")
    senha = st.sidebar.text_input("Senha", type="password")

    if st.sidebar.button("Entrar"):
        conn = conectar()
        cursor = conn.cursor()

        # Buscar usuário
        cursor.execute(
            "SELECT usuario, senha, perfil FROM usuarios WHERE usuario = ?",
            (usuario,)
        )
        user = cursor.fetchone()
        conn.close()

        if user:
            # Comparação simples (sem bcrypt)
            if senha == user["senha"]:
                st.session_state.usuario = user["usuario"]
                st.session_state.perfil = user["perfil"]
                st.sidebar.success(f"Bem-vindo, {user['usuario']}")
                return user["usuario"]
            else:
                st.sidebar.error("Senha incorreta")
        else:
            st.sidebar.error("Usuário não encontrado")

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
            st.success("Usuário cadastrado com sucesso")
        except Exception as e:
            if "UNIQUE constraint failed" in str(e):
                st.error("Usuário já existe")
            else:
                st.error(f"Erro ao cadastrar: {str(e)}")
        finally:
            conn.close()
