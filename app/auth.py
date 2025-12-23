import streamlit as st
from database import conectar, verificar_banco


def login():
    st.sidebar.subheader("Login")
    
    # Primeiro verificar se o banco está OK
    status_banco = verificar_banco()
    
    if not status_banco.get("usuarios_existe", False):
        st.sidebar.warning("⚠️ Tabela de usuários não encontrada. Clique no botão abaixo para criar.")
        if st.sidebar.button("🛠️ Criar Tabelas do Sistema"):
            from database import criar_tabelas_completas
            resultado = criar_tabelas_completas()
            if resultado.get("admin_criado"):
                st.sidebar.success("✅ Tabelas criadas! Admin: admin/sucodepao")
                st.rerun()
            else:
                st.sidebar.error("❌ Erro ao criar tabelas")
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
            # Verificar quantos usuários existem primeiro
            cursor.execute("SELECT COUNT(*) as total FROM usuarios")
            total = cursor.fetchone()["total"]
            st.sidebar.write(f"📊 Total de usuários no sistema: {total}")
            
            # Buscar usuário específico
            cursor.execute(
                "SELECT usuario, senha, perfil FROM usuarios WHERE usuario = ?",
                (usuario,)
            )
            user = cursor.fetchone()
            
            # Se não encontrou, listar todos os usuários disponíveis
            if not user:
                cursor.execute("SELECT usuario FROM usuarios")
                todos = cursor.fetchall()
                st.sidebar.info(f"Usuários disponíveis: {[u['usuario'] for u in todos]}")
            
        except Exception as e:
            st.sidebar.error(f"❌ Erro no banco de dados: {str(e)}")
            conn.close()
            return None
        
        conn.close()

        if user:
            # Comparação simples
            if senha == user["senha"]:
                st.session_state.usuario = user["usuario"]
                st.session_state.perfil = user["perfil"]
                st.sidebar.success(f"✅ Login bem-sucedido! Bem-vindo, {user['usuario']}")
                return user["usuario"]
            else:
                st.sidebar.error("❌ Senha incorreta")
        else:
            st.sidebar.error(f"❌ Usuário '{usuario}' não encontrado")

    return None


def tela_cadastro_usuario():
    st.subheader("Cadastro de Usuários")
    
    # Verificar se tabela existe
    status_banco = verificar_banco()
    if not status_banco.get("usuarios_existe", False):
        st.error("❌ Tabela de usuários não existe. Volte para a tela inicial para criar as tabelas.")
        return

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
            
            # Mostrar todos os usuários
            cursor.execute("SELECT usuario, perfil FROM usuarios")
            usuarios = cursor.fetchall()
            st.write("### 📋 Usuários cadastrados:")
            for user in usuarios:
                st.write(f"- **{user['usuario']}** ({user['perfil']})")
            
        except Exception as e:
            if "UNIQUE constraint failed" in str(e):
                st.error("❌ Usuário já existe")
            else:
                st.error(f"❌ Erro ao cadastrar: {str(e)}")
        finally:
            conn.close()
