import streamlit as st
from database import conectar
import os
import uuid

def tela_chamados(usuario, perfil):
    st.title("🔧 Chamados - DEBUG")
    
    # ========== DEBUG INFO ==========
    st.write(f"👤 Usuário atual: {usuario}")
    st.write(f"🎭 Perfil: {perfil}")
    
    # ========== TESTE DIRETO DO BANCO ==========
    st.subheader("🧪 Teste de Conexão com Banco")
    
    if st.button("Testar conexão com banco"):
        try:
            conn = conectar()
            cursor = conn.cursor()
            
            # Testar tabela usuarios
            cursor.execute("SELECT COUNT(*) as total FROM usuarios")
            total_usuarios = cursor.fetchone()["total"]
            st.success(f"✅ Tabela 'usuarios': {total_usuarios} registros")
            
            # Testar tabela chamados
            cursor.execute("SELECT COUNT(*) as total FROM chamados")
            total_chamados = cursor.fetchone()["total"]
            st.success(f"✅ Tabela 'chamados': {total_chamados} registros")
            
            # Listar últimos chamados
            cursor.execute("SELECT id, assunto, usuario FROM chamados ORDER BY id DESC LIMIT 5")
            ultimos = cursor.fetchall()
            if ultimos:
                st.write("📋 Últimos chamados:")
                for ch in ultimos:
                    st.write(f"- #{ch['id']}: {ch['assunto']} ({ch['usuario']})")
            
            conn.close()
        except Exception as e:
            st.error(f"❌ Erro no banco: {str(e)}")
    
    # ========== FORMULÁRIO SIMPLIFICADO ==========
    st.subheader("📝 Criar Chamado (Teste Simples)")
    
    with st.form("teste_chamado"):
        assunto = st.text_input("Assunto (teste)", value="TESTE " + str(st.session_state.debug_counter))
        descricao = st.text_area("Descrição", value="Esta é uma descrição de teste")
        
        if st.form_submit_button("Criar Chamado de Teste"):
            st.write("🔄 Iniciando criação do chamado...")
            
            try:
                # PASSO 1: Conectar
                conn = conectar()
                cursor = conn.cursor()
                st.write("✅ Passo 1: Conexão estabelecida")
                
                # PASSO 2: Inserir
                cursor.execute("""
                    INSERT INTO chamados (assunto, prioridade, descricao, status, usuario)
                    VALUES (?, 'Média', ?, 'Novo', ?)
                """, (assunto, descricao, usuario))
                st.write("✅ Passo 2: INSERT executado")
                
                # PASSO 3: Commit
                conn.commit()
                st.write("✅ Passo 3: COMMIT realizado")
                
                # PASSO 4: Verificar
                chamado_id = cursor.lastrowid
                st.write(f"✅ Passo 4: ID gerado = {chamado_id}")
                
                # Verificar se realmente salvou
                cursor.execute("SELECT COUNT(*) as total FROM chamados WHERE id = ?", (chamado_id,))
                verificado = cursor.fetchone()["total"]
                
                if verificado == 1:
                    st.success(f"🎉 CHAMADO #{chamado_id} SALVO COM SUCESSO!")
                    st.balloons()
                else:
                    st.error(f"❌ CHAMADO NÃO FOI SALVO! Verificado: {verificado}")
                
                conn.close()
                
            except Exception as e:
                st.error(f"❌ ERRO DETALHADO: {str(e)}")
                import traceback
                st.code(traceback.format_exc())
    
    # ========== LISTAR CHAMADOS ==========
    st.subheader("📋 Lista de Chamados")
    
    try:
        conn = conectar()
        cursor = conn.cursor()
        
        if perfil == "admin":
            cursor.execute("SELECT id, assunto, usuario, status FROM chamados ORDER BY id DESC")
        else:
            cursor.execute("SELECT id, assunto, usuario, status FROM chamados WHERE usuario = ? ORDER BY id DESC", (usuario,))
        
        chamados = cursor.fetchall()
        conn.close()
        
        if chamados:
            st.write(f"📊 Total encontrados: {len(chamados)}")
            for ch in chamados:
                st.write(f"**#{ch['id']}** - {ch['assunto']} ({ch['usuario']}) - {ch['status']}")
        else:
            st.info("📭 Nenhum chamado encontrado")
            
    except Exception as e:
        st.error(f"Erro ao listar: {str(e)}")

def garantir_pasta_uploads():
    """Função auxiliar para garantir pasta uploads."""
    uploads_dir = "uploads"
    if not os.path.exists(uploads_dir):
        os.makedirs(uploads_dir, exist_ok=True)
        st.sidebar.info(f"📁 Pasta '{uploads_dir}' criada")
    return uploads_dir
