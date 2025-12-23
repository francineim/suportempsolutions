import streamlit as st
import sqlite3
import os

# Configuração da página
st.set_page_config(
    page_title="Helpdesk MP Solutions",
    page_icon="🔧",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Título principal
st.title("🔧 Helpdesk MP Solutions")
st.markdown("---")

# ========== FUNÇÕES DO BANCO DE DADOS ==========
def criar_banco_de_dados():
    """Cria o banco de dados e tabelas se não existirem."""
    try:
        conn = sqlite3.connect("database.db")
        cursor = conn.cursor()
        
        # Tabela de usuários
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS usuarios (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                usuario TEXT UNIQUE NOT NULL,
                senha TEXT NOT NULL,
                perfil TEXT NOT NULL,
                data_cadastro TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Tabela de chamados
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS chamados (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                assunto TEXT NOT NULL,
                prioridade TEXT NOT NULL,
                descricao TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'Novo',
                usuario TEXT NOT NULL,
                data_abertura TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Verificar se já existe admin
        cursor.execute("SELECT COUNT(*) FROM usuarios WHERE usuario = 'admin'")
        if cursor.fetchone()[0] == 0:
            # Criar usuários padrão
            usuarios_base = [
                ("admin", "sucodepao", "admin"),
                ("cliente1", "senha123", "cliente"),
                ("suporte1", "senha123", "suporte")
            ]
            
            for usuario, senha, perfil in usuarios_base:
                cursor.execute(
                    "INSERT INTO usuarios (usuario, senha, perfil) VALUES (?, ?, ?)",
                    (usuario, senha, perfil)
                )
        
        conn.commit()
        conn.close()
        return True
        
    except Exception as e:
        st.error(f"Erro ao criar banco: {str(e)}")
        return False

# ========== VERIFICAÇÃO INICIAL ==========
# Verificar/Criar banco de dados
if not os.path.exists("database.db"):
    with st.spinner("🔄 Criando banco de dados..."):
        if criar_banco_de_dados():
            st.success("✅ Banco de dados criado com sucesso!")
            st.info("**Usuários disponíveis:** admin/sucodepao, cliente1/senha123, suporte1/senha123")
            st.rerun()
else:
    # Verificar conteúdo do banco
    try:
        conn = sqlite3.connect("database.db")
        cursor = conn.cursor()
        cursor.execute("SELECT usuario FROM usuarios")
        usuarios = cursor.fetchall()
        conn.close()
        
        if usuarios:
            st.sidebar.success(f"✅ Banco OK - {len(usuarios)} usuário(s)")
        else:
            st.sidebar.warning("⚠️ Banco vazio")
    except:
        st.sidebar.error("❌ Erro no banco")

# ========== SISTEMA DE LOGIN ==========
# Inicializar sessão
if 'logado' not in st.session_state:
    st.session_state.logado = False
if 'usuario' not in st.session_state:
    st.session_state.usuario = None
if 'perfil' not in st.session_state:
    st.session_state.perfil = None

# Se NÃO estiver logado, mostrar tela de login
if not st.session_state.logado:
    st.sidebar.markdown("## 🔐 Login")
    
    with st.sidebar.form("login_form"):
        usuario = st.text_input("Usuário", value="admin")
        senha = st.text_input("Senha", type="password", value="sucodepao")
        submit = st.form_submit_button("Entrar", type="primary")
        
        if submit:
            if usuario and senha:
                try:
                    conn = sqlite3.connect("database.db")
                    cursor = conn.cursor()
                    
                    cursor.execute(
                        "SELECT usuario, senha, perfil FROM usuarios WHERE usuario = ?",
                        (usuario,)
                    )
                    user = cursor.fetchone()
                    conn.close()
                    
                    if user:
                        if senha == user[1]:  # Comparar senha
                            st.session_state.logado = True
                            st.session_state.usuario = user[0]
                            st.session_state.perfil = user[2]
                            st.success(f"✅ Login realizado! Bem-vindo, {user[0]}!")
                            st.rerun()
                        else:
                            st.error("❌ Senha incorreta!")
                    else:
                        st.error("❌ Usuário não encontrado!")
                        
                        # Mostrar usuários disponíveis
                        conn = sqlite3.connect("database.db")
                        cursor = conn.cursor()
                        cursor.execute("SELECT usuario FROM usuarios")
                        todos = cursor.fetchall()
                        conn.close()
                        
                        st.info(f"Usuários disponíveis: {', '.join([u[0] for u in todos])}")
                        
                except Exception as e:
                    st.error(f"❌ Erro: {str(e)}")
            else:
                st.warning("⚠️ Preencha usuário e senha!")
    
    # Credenciais de exemplo na sidebar
    st.sidebar.markdown("---")
    st.sidebar.markdown("### 👤 Credenciais de Teste")
    st.sidebar.markdown("""
    **Administrador:**
    - Usuário: `admin`
    - Senha: `sucodepao`
    
    **Cliente:**
    - Usuário: `cliente1`
    - Senha: `senha123`
    
    **Suporte:**
    - Usuário: `suporte1`
    - Senha: `senha123`
    """)
    
    # Botão para recriar banco se necessário
    st.sidebar.markdown("---")
    if st.sidebar.button("🔄 Recriar Banco de Dados", type="secondary"):
        if os.path.exists("database.db"):
            os.remove("database.db")
        criar_banco_de_dados()
        st.success("✅ Banco recriado! Atualize a página.")
        st.rerun()

# ========== SISTEMA PRINCIPAL (se logado) ==========
else:
    # Sidebar com menu
    st.sidebar.markdown(f"## 👋 Olá, {st.session_state.usuario}!")
    st.sidebar.markdown(f"**Perfil:** {st.session_state.perfil}")
    st.sidebar.markdown("---")
    
    # Menu baseado no perfil
    menu_opcoes = ["📋 Meus Chamados", "📊 Dashboard"]
    if st.session_state.perfil == "admin":
        menu_opcoes.append("👥 Gerenciar Usuários")
    
    opcao = st.sidebar.selectbox("Menu", menu_opcoes)
    
    # Conteúdo principal baseado na opção
    if opcao == "📋 Meus Chamados":
        st.header("📋 Meus Chamados")
        
        # Formulário para novo chamado
        with st.expander("➕ Novo Chamado", expanded=True):
            with st.form("novo_chamado"):
                assunto = st.text_input("Assunto")
                prioridade = st.selectbox("Prioridade", ["Baixa", "Média", "Alta", "Urgente"])
                descricao = st.text_area("Descrição")
                
                if st.form_submit_button("Abrir Chamado"):
                    if assunto and descricao:
                        try:
                            conn = sqlite3.connect("database.db")
                            cursor = conn.cursor()
                            
                            cursor.execute("""
                                INSERT INTO chamados (assunto, prioridade, descricao, status, usuario)
                                VALUES (?, ?, ?, 'Novo', ?)
                            """, (assunto, prioridade, descricao, st.session_state.usuario))
                            
                            conn.commit()
                            chamado_id = cursor.lastrowid
                            conn.close()
                            
                            st.success(f"✅ Chamado #{chamado_id} aberto com sucesso!")
                            st.rerun()
                        except Exception as e:
                            st.error(f"❌ Erro: {str(e)}")
                    else:
                        st.warning("⚠️ Preencha todos os campos!")
        
        # Listar chamados do usuário
        st.markdown("---")
        st.subheader("Meus Chamados Abertos")
        
        try:
            conn = sqlite3.connect("database.db")
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT id, assunto, prioridade, status, data_abertura 
                FROM chamados 
                WHERE usuario = ? 
                ORDER BY data_abertura DESC
            """, (st.session_state.usuario,))
            
            chamados = cursor.fetchall()
            conn.close()
            
            if chamados:
                for chamado in chamados:
                    id_chamado, assunto, prioridade, status, data = chamado
                    
                    with st.expander(f"#{id_chamado} - {assunto}"):
                        st.write(f"**Prioridade:** {prioridade}")
                        st.write(f"**Status:** {status}")
                        st.write(f"**Data:** {data}")
            else:
                st.info("📭 Você ainda não tem chamados abertos.")
                
        except Exception as e:
            st.error(f"❌ Erro: {str(e)}")
    
    elif opcao == "📊 Dashboard":
        st.header("📊 Dashboard")
        
        try:
            conn = sqlite3.connect("database.db")
            cursor = conn.cursor()
            
            # Estatísticas
            cursor.execute("SELECT COUNT(*) FROM chamados")
            total = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM chamados WHERE status = 'Novo'")
            novos = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM chamados WHERE status = 'Em atendimento'")
            atendimento = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM chamados WHERE status = 'Concluído'")
            concluidos = cursor.fetchone()[0]
            
            conn.close()
            
            # Mostrar métricas
            col1, col2, col3, col4 = st.columns(4)
            col1.metric("Total", total)
            col2.metric("Novos", novos)
            col3.metric("Em Atendimento", atendimento)
            col4.metric("Concluídos", concluidos)
            
        except Exception as e:
            st.error(f"❌ Erro: {str(e)}")
    
    elif opcao == "👥 Gerenciar Usuários" and st.session_state.perfil == "admin":
        st.header("👥 Gerenciar Usuários")
        
        # Formulário para cadastrar novo usuário
        with st.form("cadastro_usuario"):
            st.subheader("➕ Cadastrar Novo Usuário")
            
            novo_usuario = st.text_input("Usuário")
            nova_senha = st.text_input("Senha", type="password")
            novo_perfil = st.selectbox("Perfil", ["admin", "cliente", "suporte"])
            
            if st.form_submit_button("Cadastrar"):
                if novo_usuario and nova_senha:
                    try:
                        conn = sqlite3.connect("database.db")
                        cursor = conn.cursor()
                        
                        cursor.execute(
                            "INSERT INTO usuarios (usuario, senha, perfil) VALUES (?, ?, ?)",
                            (novo_usuario, nova_senha, novo_perfil)
                        )
                        
                        conn.commit()
                        conn.close()
                        
                        st.success(f"✅ Usuário '{novo_usuario}' cadastrado!")
                        st.rerun()
                    except Exception as e:
                        if "UNIQUE constraint failed" in str(e):
                            st.error("❌ Usuário já existe!")
                        else:
                            st.error(f"❌ Erro: {str(e)}")
                else:
                    st.warning("⚠️ Preencha todos os campos!")
        
        # Listar usuários existentes
        st.markdown("---")
        st.subheader("📋 Usuários Cadastrados")
        
        try:
            conn = sqlite3.connect("database.db")
            cursor = conn.cursor()
            
            cursor.execute("SELECT usuario, perfil, data_cadastro FROM usuarios ORDER BY usuario")
            usuarios = cursor.fetchall()
            conn.close()
            
            if usuarios:
                for user in usuarios:
                    st.write(f"**{user[0]}** - {user[1]} (desde {user[2]})")
            else:
                st.info("Nenhum usuário cadastrado.")
                
        except Exception as e:
            st.error(f"❌ Erro: {str(e)}")
    
    # Botão de logout
    st.sidebar.markdown("---")
    if st.sidebar.button("🚪 Logout", type="secondary"):
        st.session_state.logado = False
        st.session_state.usuario = None
        st.session_state.perfil = None
        st.rerun()

# ========== RODAPÉ ==========
st.markdown("---")
st.markdown("🔧 **Helpdesk MP Solutions** | Sistema de suporte técnico")
