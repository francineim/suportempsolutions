import streamlit as st
import sqlite3
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
