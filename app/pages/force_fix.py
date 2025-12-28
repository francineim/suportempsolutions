# app/pages/force_fix.py
"""
Force Fix - Ferramenta de correção do banco de dados
Apenas para administradores
"""

import streamlit as st
import sqlite3
import os
import shutil
from datetime import datetime

def fix_database():
    """Ferramenta de correção e manutenção do banco de dados."""
    st.subheader("🔧 Force Fix - Manutenção do Sistema")
    
    st.warning("⚠️ **ATENÇÃO:** Esta ferramenta é destinada apenas para administradores. Use com cuidado!")
    
    # Abas de funcionalidades
    tab_diagnostico, tab_correcoes, tab_backup, tab_email = st.tabs([
        "🔍 Diagnóstico",
        "🛠️ Correções",
        "💾 Backup/Restore",
        "📧 Teste de E-mail"
    ])
    
    # ========== TAB: DIAGNÓSTICO ==========
    with tab_diagnostico:
        st.write("### 🔍 Diagnóstico do Sistema")
        
        if st.button("🔍 Executar Diagnóstico Completo", type="primary"):
            with st.spinner("Analisando banco de dados..."):
                try:
                    conn = sqlite3.connect("data/database.db")
                    conn.row_factory = sqlite3.Row
                    cursor = conn.cursor()
                    
                    # Verificar tabelas
                    st.write("**📋 Tabelas no banco:**")
                    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
                    tabelas = [row[0] for row in cursor.fetchall()]
                    
                    for tabela in tabelas:
                        cursor.execute(f"SELECT COUNT(*) FROM {tabela}")
                        count = cursor.fetchone()[0]
                        st.write(f"  ✅ `{tabela}`: {count} registros")
                    
                    # Verificar integridade
                    st.write("")
                    st.write("**🔒 Verificação de Integridade:**")
                    cursor.execute("PRAGMA integrity_check")
                    resultado = cursor.fetchone()[0]
                    
                    if resultado == "ok":
                        st.success("✅ Banco de dados íntegro!")
                    else:
                        st.error(f"❌ Problemas encontrados: {resultado}")
                    
                    # Verificar índices
                    st.write("")
                    st.write("**📊 Índices:**")
                    cursor.execute("SELECT name FROM sqlite_master WHERE type='index'")
                    indices = [row[0] for row in cursor.fetchall()]
                    st.write(f"  Total de índices: {len(indices)}")
                    
                    # Tamanho do banco
                    st.write("")
                    st.write("**💾 Tamanho do banco:**")
                    if os.path.exists("data/database.db"):
                        tamanho = os.path.getsize("data/database.db")
                        st.write(f"  {tamanho / 1024:.2f} KB")
                    
                    conn.close()
                    st.success("✅ Diagnóstico concluído!")
                    
                except Exception as e:
                    st.error(f"❌ Erro no diagnóstico: {e}")
    
    # ========== TAB: CORREÇÕES ==========
    with tab_correcoes:
        st.write("### 🛠️ Correções Disponíveis")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.write("**🔄 Recriar Tabelas Faltantes**")
            if st.button("Executar", key="btn_recriar_tabelas"):
                try:
                    from database import criar_tabelas
                    resultado = criar_tabelas()
                    if resultado:
                        st.success("✅ Tabelas verificadas/criadas!")
                    else:
                        st.error("❌ Erro ao criar tabelas")
                except Exception as e:
                    st.error(f"Erro: {e}")
        
        with col2:
            st.write("**🧹 Limpar Tabela de Logs**")
            if st.button("Executar", key="btn_limpar_logs"):
                try:
                    conn = sqlite3.connect("data/database.db")
                    cursor = conn.cursor()
                    cursor.execute("DELETE FROM logs_sistema WHERE data_hora < datetime('now', '-30 days')")
                    excluidos = cursor.rowcount
                    conn.commit()
                    conn.close()
                    st.success(f"✅ {excluidos} logs antigos removidos!")
                except Exception as e:
                    st.error(f"Erro: {e}")
        
        st.divider()
        
        st.write("**🔧 Adicionar Colunas Faltantes**")
        if st.button("Verificar e Adicionar Colunas", key="btn_add_colunas"):
            try:
                conn = sqlite3.connect("data/database.db")
                cursor = conn.cursor()
                
                # Lista de colunas que devem existir
                colunas_esperadas = {
                    'chamados': [
                        ('data_ultima_atualizacao', 'TIMESTAMP DEFAULT CURRENT_TIMESTAMP'),
                        ('tempo_atendimento_segundos', 'INTEGER DEFAULT 0'),
                        ('status_atendimento', "TEXT DEFAULT 'nao_iniciado'"),
                        ('ultima_retomada', 'TIMESTAMP'),
                        ('retornos', 'INTEGER DEFAULT 0')
                    ],
                    'usuarios': [
                        ('ultimo_acesso', 'TIMESTAMP'),
                        ('ativo', 'INTEGER DEFAULT 1')
                    ],
                    'anexos': [
                        ('tamanho_bytes', 'INTEGER'),
                        ('tipo_arquivo', 'TEXT')
                    ]
                }
                
                for tabela, colunas in colunas_esperadas.items():
                    for col_nome, col_tipo in colunas:
                        try:
                            cursor.execute(f"ALTER TABLE {tabela} ADD COLUMN {col_nome} {col_tipo}")
                            st.write(f"  ✅ Adicionada: {tabela}.{col_nome}")
                        except sqlite3.OperationalError as e:
                            if "duplicate column" in str(e).lower():
                                st.write(f"  ✓ Já existe: {tabela}.{col_nome}")
                            else:
                                st.write(f"  ⚠️ {tabela}.{col_nome}: {e}")
                
                conn.commit()
                conn.close()
                st.success("✅ Verificação de colunas concluída!")
                
            except Exception as e:
                st.error(f"Erro: {e}")
        
        st.divider()
        
        st.write("**⚡ Otimizar Banco de Dados**")
        if st.button("Executar VACUUM", key="btn_vacuum"):
            try:
                conn = sqlite3.connect("data/database.db")
                conn.execute("VACUUM")
                conn.close()
                st.success("✅ Banco otimizado!")
            except Exception as e:
                st.error(f"Erro: {e}")
    
    # ========== TAB: BACKUP ==========
    with tab_backup:
        st.write("### 💾 Backup e Restauração")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.write("**📤 Criar Backup**")
            
            if st.button("💾 Criar Backup Agora", type="primary"):
                try:
                    if not os.path.exists("backups"):
                        os.makedirs("backups")
                    
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    backup_path = f"backups/database_backup_{timestamp}.db"
                    
                    shutil.copy2("data/database.db", backup_path)
                    
                    st.success(f"✅ Backup criado: {backup_path}")
                    
                    # Oferecer download
                    with open(backup_path, 'rb') as f:
                        st.download_button(
                            "⬇️ Baixar Backup",
                            f.read(),
                            f"database_backup_{timestamp}.db",
                            "application/octet-stream"
                        )
                except Exception as e:
                    st.error(f"Erro: {e}")
        
        with col2:
            st.write("**📥 Restaurar Backup**")
            
            arquivo_backup = st.file_uploader(
                "Selecione o arquivo de backup",
                type=['db'],
                key="upload_backup"
            )
            
            if arquivo_backup:
                st.warning("⚠️ Isso substituirá TODOS os dados atuais!")
                confirmar = st.checkbox("Confirmo que quero restaurar o backup")
                
                if confirmar:
                    if st.button("🔄 Restaurar", type="secondary"):
                        try:
                            # Backup do atual antes de restaurar
                            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                            if not os.path.exists("backups"):
                                os.makedirs("backups")
                            shutil.copy2("data/database.db", f"backups/pre_restore_{timestamp}.db")
                            
                            # Restaurar
                            with open("data/database.db", 'wb') as f:
                                f.write(arquivo_backup.read())
                            
                            st.success("✅ Backup restaurado com sucesso!")
                            st.info("Recarregue a página para ver as alterações.")
                        except Exception as e:
                            st.error(f"Erro: {e}")
        
        st.divider()
        
        # Listar backups existentes
        st.write("**📋 Backups Existentes:**")
        if os.path.exists("backups"):
            backups = sorted([f for f in os.listdir("backups") if f.endswith('.db')], reverse=True)
            if backups:
                for backup in backups[:10]:  # Mostrar últimos 10
                    caminho = f"backups/{backup}"
                    tamanho = os.path.getsize(caminho) / 1024
                    st.write(f"  📄 {backup} ({tamanho:.1f} KB)")
            else:
                st.info("Nenhum backup encontrado")
        else:
            st.info("Pasta de backups não existe")
    
    # ========== TAB: TESTE DE E-MAIL ==========
    with tab_email:
        st.write("### 📧 Teste de Configuração de E-mail")
        
        try:
            from config.email_config import get_email_status, EMAIL_ENABLED
            
            status = get_email_status()
            
            st.write("**Status Atual:**")
            col1, col2 = st.columns(2)
            
            with col1:
                st.write(f"  Habilitado: {'✅ Sim' if status['habilitado'] else '❌ Não'}")
                st.write(f"  Configurado: {'✅ Sim' if status['configurado'] else '❌ Não'}")
            
            with col2:
                st.write(f"  SMTP: {status['smtp_host']}:{status['smtp_port']}")
                st.write(f"  Usuário: {status['smtp_user']}")
            
            if not status['configurado']:
                st.warning(f"⚠️ {status['mensagem']}")
                st.info("""
                **Para configurar e-mail, adicione em `.streamlit/secrets.toml`:**
                ```toml
                SMTP_HOST = "smtp.office365.com"
                SMTP_PORT = "587"
                SMTP_USER = "seu-email@dominio.com"
                SMTP_PASSWORD = "sua-senha"
                EMAIL_FROM_ADDRESS = "seu-email@dominio.com"
                EMAIL_ADMIN = "admin@dominio.com"
                EMAIL_ENABLED = "true"
                ```
                """)
            
            st.divider()
            
            st.write("**📤 Enviar E-mail de Teste:**")
            
            email_teste = st.text_input("E-mail de destino", key="email_teste")
            
            if st.button("📤 Enviar Teste", disabled=not EMAIL_ENABLED):
                if not email_teste:
                    st.error("Informe um e-mail de destino")
                else:
                    try:
                        from email_system.email_service import enviar_email
                        
                        corpo = """
                        <html>
                        <body>
                            <h2>✅ Teste de Configuração</h2>
                            <p>Este é um e-mail de teste do Sistema Helpdesk.</p>
                            <p>Se você recebeu este e-mail, a configuração está correta!</p>
                            <hr>
                            <p><small>Helpdesk – MP Solutions</small></p>
                        </body>
                        </html>
                        """
                        
                        sucesso, msg = enviar_email(
                            email_teste,
                            "Teste - Helpdesk MP Solutions",
                            corpo
                        )
                        
                        if sucesso:
                            st.success(f"✅ {msg}")
                        else:
                            st.error(f"❌ {msg}")
                    except Exception as e:
                        st.error(f"Erro: {e}")
            
            if not EMAIL_ENABLED:
                st.info("💡 Defina `EMAIL_ENABLED = true` nos secrets para habilitar o envio.")
                
        except Exception as e:
            st.error(f"Erro ao carregar configurações de e-mail: {e}")
