import streamlit as st
from database import conectar

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
                "SELECT usuario, senha, perfil FROM usuarios WHERE usuario = ?",
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
                st.sidebar.error("Usuário não encontrado")
                
        except Exception as e:
            st.sidebar.error(f"Erro no login: {str(e)}")
        finally:
            conn.close()
    
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
