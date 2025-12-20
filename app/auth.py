import streamlit as st
from database import conectar


def login():
    st.sidebar.subheader("Login")

    usuario = st.sidebar.text_input("Usuário")
    senha = st.sidebar.text_input("Senha", type="password")

    if st.sidebar.button("Entrar"):
        conn = conectar()
        cursor = conn.cursor()

        cursor.execute(
            "SELECT usuario, perfil FROM usuarios WHERE usuario = ? AND senha = ?",
            (usuario, senha)
        )
        user = cursor.fetchone()
        conn.close()

        if user:
            st.session_state.usuario = user["usuario"]
            st.session_state.perfil = user["perfil"]
            st.sidebar.success(f"Bem-vindo, {user['usuario']}")
            return user["usuario"]
        else:
            st.sidebar.error("Usuário ou senha inválidos")

    return None


def tela_cadastro_usuario():
    st.subheader("Cadastro de Usuários")

    usuario = st.text_input("Usuário")
    senha = st.text_input("Senha", type="password")
    perfil = st.selectbox("Perfil", ["admin", "cliente", "suporte"])

    if st.button("Cadastrar usuário"):
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
            st.error("Usuário já existe ou erro ao cadastrar")
        finally:
            conn.close()
