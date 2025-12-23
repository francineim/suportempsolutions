import streamlit as st
import sqlite3
import os

def fix_database():
    """Força a correção do banco de dados."""
    st.title("🔨 Correção Forçada do Banco de Dados")
    
    st.info("""
    **Status atual:** A tabela 'usuarios' NÃO EXISTE no banco de dados.
    
    **Ação:** Vou criar todo o sistema do zero com estrutura correta.
    """)
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("🚀 CRIAR SISTEMA COMPLETO", type="primary"):
            criar_sistema_completo()
    
    with col2:
        if st.button("📋 APENAS VERIFICAR", type="secondary"):
            verificar_estado_atual()


def verificar_estado_atual():
    """Apenas verifica o estado atual do banco."""
    try:
        conn = sqlite3.connect("database.db")
        cursor = conn.cursor()
        
        # Verificar quais tabelas existem
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tabelas = cursor.fetchall()
        
        st.write("## 📊 Estado Atual do Banco")
        
        if not tabelas:
            st.error("❌ Nenhuma tabela encontrada no banco!")
        else:
            st.success(f"✅ Encontradas {len(tabelas)} tabela(s):")
            for tabela in tabelas:
                st.write(f"- **{tabela[0]}**")
                
                # Mostrar estrutura de cada tabela
                cursor.execute(f"PRAGMA table_info({tabela[0]})")
                colunas = cursor.fetchall()
                
                st.write(f"  Colunas:")
                for col in colunas:
                    st.write(f"  - {col[1]} ({col[2]})")
        
        conn.close()
        
    except Exception as e:
        st.error(f"❌ Erro ao verificar: {str(e)}")


def criar_sistema_completo():
    """Cria todo o sistema do zero."""
    try:
        # Passo 1: Remover arquivo antigo se existir
        if os.path.exists("database.db"):
            os.remove("database.db")
            st.success("✅ Arquivo database.db antigo removido")
        
        # Passo 2: Criar novo banco
        conn = sqlite3.connect("database.db")
        cursor = conn.cursor()
        
        st.write("## 🏗️ Criando tabelas...")
        
        # Tabela de usuários COM COLUNA 'senha'
        cursor.execute("""
            CREATE TABLE usuarios (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                usuario TEXT UNIQUE NOT NULL,
                senha TEXT NOT NULL,
                perfil TEXT NOT NULL,
                data_cadastro TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        st.success("✅ Tabela 'usuarios' criada")
        
        # Tabela de chamados
        cursor.execute("""
            CREATE TABLE chamados (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                assunto TEXT NOT NULL,
                prioridade TEXT NOT NULL,
                descricao TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'Novo',
                usuario TEXT NOT NULL,
                data_abertura TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        st.success("✅ Tabela 'chamados' criada")
        
        # Passo 3: Criar usuários padrão
        st.write("## 👥 Criando usuários padrão...")
        
        usuarios_padrao = [
            ("admin", "sucodepao", "admin"),
            ("cliente1", "senha123", "cliente"),
            ("suporte1", "senha123", "suporte"),
            ("joao", "senha123", "cliente"),
            ("maria", "senha123", "suporte")
        ]
        
        for usuario, senha, perfil in usuarios_padrao:
            cursor.execute(
                "INSERT INTO usuarios (usuario, senha, perfil) VALUES (?, ?, ?)",
                (usuario, senha, perfil)
            )
            st.write(f"✅ {usuario} ({perfil}) - senha: {senha}")
        
        # Passo 4: Verificar estrutura
        st.write("## 🔍 Verificando estrutura...")
        
        cursor.execute("PRAGMA table_info(usuarios)")
        colunas_usuarios = cursor.fetchall()
        
        st.success("**Estrutura da tabela 'usuarios':**")
        for col in colunas_usuarios:
            st.write(f"- **{col[1]}** ({col[2]})")
        
        # Contar registros
        cursor.execute("SELECT COUNT(*) FROM usuarios")
        total_usuarios = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM chamados")
        total_chamados = cursor.fetchone()[0]
        
        # Listar usuários criados
        cursor.execute("SELECT usuario, perfil FROM usuarios ORDER BY usuario")
        usuarios = cursor.fetchall()
        
        conn.commit()
        conn.close()
        
        # Passo 5: Resultado final
        st.write("## 🎉 Sistema Criado com Sucesso!")
        
        st.success(f"""
        **Resumo:**
        - ✅ Usuários criados: {total_usuarios}
        - ✅ Tabelas criadas: 2 (usuarios, chamados)
        - ✅ Chamados: {total_chamados}
        """)
        
        st.write("**📋 Usuários disponíveis para login:**")
        for usuario, perfil in usuarios:
            st.write(f"- **{usuario}** ({perfil})")
        
        st.write("""
        **🔑 Credenciais principais:**
        - **admin** / **sucodepao** (administrador)
        - **cliente1** / **senha123** (cliente)
        - **suporte1** / **senha123** (suporte)
        """)
        
        st.balloons()
        
        # Botão para voltar ao login
        if st.button("🔙 Voltar para Login", type="primary"):
            # Redirecionar para página principal
            st.switch_page("app/main.py")
        
    except Exception as e:
        st.error(f"❌ Erro ao criar sistema: {str(e)}")
        import traceback
        st.code(traceback.format_exc())


def main():
    """Página principal da correção."""
    st.set_page_config(
        page_title="Correção Banco - Helpdesk",
        layout="wide"
    )
    
    fix_database()


if __name__ == "__main__":
    main()
