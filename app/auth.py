import streamlit as st
from database import conectar, criar_banco_se_nao_existir, verificar_estrutura


def login():
    st.sidebar.subheader("Login")
    
    # Criar banco se não existir
    banco_novo = criar_banco_se_nao_existir()
    if banco_novo:
        st.sidebar.success("✅ Banco de dados criado! Admin: admin/sucodepao")
    
    # Verificar estrutura
    estrutura = verificar_estrutura()
    if estrutura["status"] == "error":
        st.sidebar.error(f"❌ {estrutura['message']}")
        st.sidebar.info("Use o botão 'Resetar Banco' para corrigir")
        return None
    
    usuario = st.sidebar.text_input("Usuário")
    senha = st.sidebar.text_input("Senha", type="password")

    if st.sidebar.button("Entrar"):
        if not usuario or not senha:
            st.sidebar.error("Por favor, preencha todos os campos")
            return None
        
        conn = conectar()
        cursor = conn.cursor()

        try:
            # Buscar usuário (USANDO 'senha', não 'senha_hash')
            cursor.execute(
                "SELECT usuario, senha, perfil FROM usuarios WHERE usuario = ?",
                (usuario,)
            )
            user = cursor.fetchone()
            
        except Exception as e:
            st.sidebar.error(f"❌ Erro no banco: {str(e)}")
            # DEBUG: Mostrar erro completo
            import traceback
            st.sidebar.code(traceback.format_exc())
            conn.close()
            return None
        
        conn.close()

        if user:
            # Comparação SIMPLES - senha em texto
            if senha == user[1]:  # user[1] é a senha
                st.session_state.usuario = user[0]  # user[0] é o usuário
                st.session_state.perfil = user[2]   # user[2] é o perfil
                st.sidebar.success(f"✅ Login bem-sucedido!")
                return user[0]
            else:
                st.sidebar.error("❌ Senha incorreta")
        else:
            # Mostrar usuários disponíveis
            conn = conectar()
            cursor = conn.cursor()
            cursor.execute("SELECT usuario FROM usuarios")
            todos = cursor.fetchall()
            conn.close()
            
            usuarios_disponiveis = [u[0] for u in todos]
            st.sidebar.error(f"❌ Usuário não encontrado. Disponíveis: {', '.join(usuarios_disponiveis)}")

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
            st.success(f"✅ Usuário '{usuario}' cadastrado!")
            
        except Exception as e:
            if "UNIQUE constraint failed" in str(e):
                st.error("❌ Usuário já existe")
            else:
                st.error(f"❌ Erro: {str(e)}")
        finally:
            conn.close()
