import streamlit as st
import sqlite3
import os

def resetar_banco_completo():
    """Reseta completamente o banco de dados (APENAS PARA EMERGÊNCIAS)."""
    
    st.warning("⚠️ **ATENÇÃO:** Esta ação vai APAGAR TODOS OS DADOS do sistema!")
    
    if st.button("🔥 RESETAR BANCO DE DADOS COMPLETAMENTE", type="secondary"):
        try:
            # Remover arquivo do banco se existir
            if os.path.exists("database.db"):
                os.remove("database.db")
                st.success("✅ Arquivo database.db removido")
            
            # Criar novo banco com estrutura SIMPLES
            conn = sqlite3.connect("database.db", check_same_thread=False)
            cursor = conn.cursor()
            
            # Tabela de usuários (SEMPRE com coluna 'senha', NUNCA 'senha_hash')
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
            
            # Inserir admin padrão
            cursor.execute(
                "INSERT INTO usuarios (usuario, senha, perfil) VALUES (?, ?, ?)",
                ("admin", "sucodepao", "admin")
            )
            
            # Inserir alguns usuários de exemplo
            cursor.execute(
                "INSERT INTO usuarios (usuario, senha, perfil) VALUES (?, ?, ?)",
                ("cliente1", "senha123", "cliente")
            )
            
            cursor.execute(
                "INSERT INTO usuarios (usuario, senha, perfil) VALUES (?, ?, ?)",
                ("suporte1", "senha123", "suporte")
            )
            
            conn.commit()
            conn.close()
            
            st.success("""
            ✅ **Banco de dados resetado com sucesso!**
            
            **Usuários criados:**
            1. admin / sucodepao (perfil: admin)
            2. cliente1 / senha123 (perfil: cliente)
            3. suporte1 / senha123 (perfil: suporte)
            
            **Estrutura correta garantida:**
            - Tabela 'usuarios' com coluna 'senha' (NÃO 'senha_hash')
            - Tabela 'chamados' pronta para uso
            """)
            
            # Verificar a estrutura
            conn = sqlite3.connect("database.db", check_same_thread=False)
            cursor = conn.cursor()
            
            cursor.execute("PRAGMA table_info(usuarios)")
            colunas = cursor.fetchall()
            
            st.write("**Estrutura da tabela 'usuarios':**")
            for col in colunas:
                st.write(f"- {col[1]} ({col[2]})")
            
            conn.close()
            
        except Exception as e:
            st.error(f"❌ Erro ao resetar banco: {str(e)}")

if __name__ == "__main__":
    resetar_banco_completo()
