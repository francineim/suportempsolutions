import streamlit as st
import sqlite3
import os

def fix_database():
    """Força a correção do banco de dados."""
    st.title("🔨 Correção Forçada do Banco de Dados")
    
    st.warning("""
    **ATENÇÃO:** Esta ação vai:
    1. Backup dos dados existentes
    2. Recriar a tabela com estrutura correta
    3. Restaurar usuários com senhas padrão
    """)
    
    if st.button("🚀 EXECUTAR CORREÇÃO COMPLETA", type="primary"):
        try:
            # Passo 1: Fazer backup dos dados existentes
            conn = sqlite3.connect("database.db")
            cursor = conn.cursor()
            
            # Obter dados atuais
            cursor.execute("SELECT usuario, perfil FROM usuarios")
            usuarios_backup = cursor.fetchall()
            
            st.write(f"📦 Backup de {len(usuarios_backup)} usuários realizado")
            
            # Listar usuários no backup
            for usuario, perfil in usuarios_backup:
                st.write(f"- {usuario} ({perfil})")
            
            conn.close()
            
            # Passo 2: Remover arquivo do banco
            if os.path.exists("database.db"):
                os.remove("database.db")
                st.success("✅ Arquivo database.db removido")
            
            # Passo 3: Criar novo banco com estrutura CORRETA
            conn = sqlite3.connect("database.db")
            cursor = conn.cursor()
            
            # Tabela de usuários COM COLUNA 'senha' (não 'senha_hash')
            cursor.execute("""
                CREATE TABLE usuarios (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    usuario TEXT UNIQUE NOT NULL,
                    senha TEXT NOT NULL,
                    perfil TEXT NOT NULL,
                    data_cadastro TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
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
            
            # Passo 4: Restaurar usuários com senhas padrão
            for usuario, perfil in usuarios_backup:
                if usuario == 'admin':
                    senha = 'sucodepao'
                else:
                    senha = 'senha123'
                
                cursor.execute(
                    "INSERT INTO usuarios (usuario, senha, perfil) VALUES (?, ?, ?)",
                    (usuario, senha, perfil)
                )
                st.write(f"✅ Restaurado: {usuario} com senha: {senha}")
            
            # Se não tinha admin, criar
            cursor.execute("SELECT COUNT(*) FROM usuarios WHERE usuario = 'admin'")
            if cursor.fetchone()[0] == 0:
                cursor.execute(
                    "INSERT INTO usuarios (usuario, senha, perfil) VALUES (?, ?, ?)",
                    ("admin", "sucodepao", "admin")
                )
                st.write("✅ Admin criado: admin / sucodepao")
            
            conn.commit()
            
            # Passo 5: Verificar estrutura final
            cursor.execute("PRAGMA table_info(usuarios)")
            colunas = cursor.fetchall()
            
            st.success("""
            🎉 **CORREÇÃO CONCLUÍDA COM SUCESSO!**
            
            **Estrutura da tabela 'usuarios':**
            """)
            
            for col in colunas:
                st.write(f"- **{col[1]}** ({col[2]})")
            
            # Listar todos os usuários
            cursor.execute("SELECT usuario, perfil FROM usuarios")
            usuarios_finais = cursor.fetchall()
            
            st.write("**👥 Usuários disponíveis:**")
            for usuario, perfil in usuarios_finais:
                st.write(f"- **{usuario}** ({perfil})")
            
            conn.close()
            
            st.balloons()
            st.success("""
            ✅ **Pronto para usar!**
            
            **Credenciais:**
            - admin / sucodepao
            - Outros usuários: username / senha123
            
            **Volte para a página principal e faça login.**
            """)
            
        except Exception as e:
            st.error(f"❌ Erro durante correção: {str(e)}")
            import traceback
            st.code(traceback.format_exc())

if __name__ == "__main__":
    fix_database()
