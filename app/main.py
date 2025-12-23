import streamlit as st
import sqlite3
import os

st.set_page_config(
    page_title="Helpdesk MP Solutions",
    layout="wide",
    initial_sidebar_state="expanded"
)

# DEBUG: Mostrar que estamos na página principal
st.title("🔧 Helpdesk MP Solutions - DEBUG MODE")

# Mostrar informações da sessão
st.write("### 🧪 Informações da Sessão:")
st.write(f"- Usuário na sessão: `{st.session_state.get('usuario', 'NÃO LOGADO')}`")
st.write(f"- Perfil na sessão: `{st.session_state.get('perfil', 'NÃO DEFINIDO')}`")

# Verificar se arquivo do banco existe
st.write("### 📁 Verificação do Banco de Dados:")
if os.path.exists("database.db"):
    st.success("✅ Arquivo database.db EXISTE")
    
    try:
        conn = sqlite3.connect("database.db")
        cursor = conn.cursor()
        
        # Verificar tabelas
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tabelas = cursor.fetchall()
        
        if tabelas:
            st.success(f"✅ {len(tabelas)} tabela(s) encontrada(s):")
            for tabela in tabelas:
                st.write(f"  - **{tabela[0]}**")
                
                # Verificar conteúdo da tabela usuarios
                if tabela[0] == 'usuarios':
                    cursor.execute("SELECT COUNT(*) FROM usuarios")
                    total = cursor.fetchone()[0]
                    st.write(f"    👥 {total} usuário(s) cadastrado(s)")
                    
                    cursor.execute("SELECT usuario, perfil FROM usuarios")
                    usuarios = cursor.fetchall()
                    for user in usuarios:
                        st.write(f"    - {user[0]} ({user[1]})")
        
        conn.close()
    except Exception as e:
        st.error(f"❌ Erro ao acessar banco: {str(e)}")
else:
    st.error("❌ Arquivo database.db NÃO ENCONTRADO")

# Agora a parte do login (versão SIMPLES para debug)
st.write("### 🔐 Tela de Login (Debug)")

with st.sidebar:
    st.subheader("Login Debug")
    
    usuario = st.text_input("Usuário", key="debug_user")
    senha = st.text_input("Senha", type="password", key="debug_pass")
    
    if st.button("Testar Login", type="primary"):
        st.write("### 📊 Resultado do Teste:")
        st.write(f"- Usuário digitado: `{usuario}`")
        st.write(f"- Senha digitada: `{senha}`")
        
        if usuario and senha:
            try:
                conn = sqlite3.connect("database.db")
                cursor = conn.cursor()
                
                # Buscar usuário
                cursor.execute(
                    "SELECT usuario, senha, perfil FROM usuarios WHERE usuario = ?",
                    (usuario,)
                )
                user = cursor.fetchone()
                
                if user:
                    st.success(f"✅ Usuário ENCONTRADO no banco: {user[0]}")
                    st.write(f"- Senha no banco: `{user[1]}`")
                    st.write(f"- Perfil: `{user[2]}`")
                    
                    # Comparar senhas
                    if senha == user[1]:
                        st.success("🎉 **SENHA CORRETA! Login bem-sucedido!**")
                        
                        # Armazenar na sessão
                        st.session_state.usuario = user[0]
                        st.session_state.perfil = user[2]
                        
                        st.write("### 🔄 Próximos passos:")
                        st.write("1. Página será recarregada automaticamente")
                        st.write("2. Você verá o menu completo do sistema")
                        st.rerun()
                    else:
                        st.error(f"❌ Senha INCORRETA. Digite: `{user[1]}`")
                else:
                    st.error("❌ Usuário NÃO ENCONTRADO no banco")
                    
                    # Listar usuários disponíveis
                    cursor.execute("SELECT usuario FROM usuarios")
                    todos = cursor.fetchall()
                    st.write("**Usuários disponíveis:**")
                    for u in todos:
                        st.write(f"- `{u[0]}`")
                
                conn.close()
                
            except Exception as e:
                st.error(f"❌ Erro no banco: {str(e)}")
        else:
            st.warning("⚠️ Preencha usuário e senha")

# Se já estiver logado, mostrar menu
if st.session_state.get('usuario'):
    st.sidebar.success(f"👋 Olá, {st.session_state.usuario}!")
    
    st.write("### 🎉 LOGIN REALIZADO COM SUCESSO!")
    st.write(f"**Usuário:** {st.session_state.usuario}")
    st.write(f"**Perfil:** {st.session_state.perfil}")
    
    # Botão de logout
    if st.sidebar.button("🚪 Logout"):
        st.session_state.usuario = None
        st.session_state.perfil = None
        st.rerun()
