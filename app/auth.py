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
            "SELECT usuario, senha, perfil FROM usuarios WHERE usuario = ?",
            (usuario,)
        )
        user = cursor.fetchone()
        conn.close()

        if user:
            if senha == user["senha"]:
                st.session_state.usuario = user["usuario"]
                st.session_state.perfil = user["perfil"]
                st.sidebar.success(f"Bem-vindo, {user['usuario']}!")
                return user["usuario"]
            else:
                st.sidebar.error("Senha incorreta")
        else:
            st.sidebar.error("Usuário não encontrado")

    return None

def tela_cadastro_usuario():
    # ... (mantenha o mesmo código que já tinha)
