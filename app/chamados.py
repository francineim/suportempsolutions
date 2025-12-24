import streamlit as st
from database import conectar, buscar_chamados, buscar_descricao_chamado, salvar_anexo, buscar_anexos
import os
import uuid

def tela_chamados(usuario, perfil):
    st.subheader("Chamados")
    
    # ========== NOVO CHAMADO ==========
    with st.expander("➕ Novo chamado"):
        with st.form("form_novo_chamado", clear_on_submit=True):
            assunto = st.text_input("Assunto")
            prioridade = st.selectbox("Prioridade", ["Baixa", "Média", "Alta", "Urgente"])
            descricao = st.text_area("Descrição do problema")
            
            # Upload de arquivo
            st.write("📎 Anexar arquivo (opcional):")
            arquivo = st.file_uploader(
                "Selecione um arquivo",
                type=['pdf', 'doc', 'docx', 'xls', 'xlsx', 'txt', 'jpg', 'png', 'jpeg'],
                key="novo_chamado_file"
            )
            
            submitted = st.form_submit_button("Abrir chamado")
            
            if submitted:
                if assunto and descricao:
                    conn = None
                    try:
                        conn = conectar()
                        cursor = conn.cursor()
                        
                        # Inserir chamado
                        cursor.execute("""
                            INSERT INTO chamados 
                            (assunto, prioridade, descricao, status, usuario)
                            VALUES (?, ?, ?, 'Novo', ?)
                        """, (assunto, prioridade, descricao, usuario))
                        
                        conn.commit()
                        chamado_id = cursor.lastrowid
                        
                        # Salvar anexo se houver
                        if arquivo is not None:
                            # Garantir pasta uploads
                            if not os.path.exists("uploads"):
                                os.makedirs("uploads")
                            
                            # Gerar nome único
                            file_ext = os.path.splitext(arquivo.name)[1]
                            unique_name = f"{uuid.uuid4()}{file_ext}"
                            file_path = os.path.join("uploads", unique_name)
                            
                            # Salvar arquivo
                            with open(file_path, "wb") as f:
                                f.write(arquivo.getbuffer())
                            
                            # Salvar no banco
                            salvar_anexo(chamado_id, arquivo.name, file_path)
                        
                        st.success(f"✅ Chamado #{chamado_id} aberto com sucesso!")
                        
                    except Exception as e:
                        st.error(f"❌ Erro ao abrir chamado: {str(e)}")
                        if conn:
                            conn.rollback()
                    finally:
                        if conn:
                            conn.close()
                else:
                    st.error("⚠️ Preencha o assunto e a descrição")
    
    st.divider()
    
    # ========== LISTA DE CHAMADOS ==========
    try:
        chamados = buscar_chamados(usuario, perfil)
        
        if not chamados:
            st.info("📭 Nenhum chamado encontrado")
        else:
            st.write(f"📊 Total: {len(chamados)}")
            
            for ch in chamados:
                with st.expander(f"#{ch['id']} - {ch['assunto']}"):
                    st.write(f"📌 Prioridade: {ch['prioridade']}")
                    st.write(f"📍 Status: {ch['status']}")
                    st.write(f"👤 Usuário: {ch['usuario']}")
                    st.write(f"📅 Abertura: {ch['data_abertura']}")
                    
                    # Descrição
                    st.divider()
                    st.write("**Descrição:**")
                    descricao_completa = buscar_descricao_chamado(ch['id'])
                    st.write(descricao_completa)
                    
                    # Anexos
                    st.divider()
                    st.write("**📎 Anexos:**")
                    
                    anexos = buscar_anexos(ch['id'])
                    
                    if anexos:
                        for anexo in anexos:
                            col_a, col_b = st.columns([3, 1])
                            
                            with col_a:
                                st.write(f"📄 {anexo['nome_arquivo']}")
                                st.caption(f"Adicionado: {anexo['data_upload']}")
                            
                            with col_b:
                                # Download
                                if os.path.exists(anexo['caminho_arquivo']):
                                    with open(anexo['caminho_arquivo'], 'rb') as f:
                                        st.download_button(
                                            label="⬇️ Download",
                                            data=f.read(),
                                            file_name=anexo['nome_arquivo'],
                                            key=f"dl_{anexo['id']}"
                                        )
                    else:
                        st.write("Nenhum anexo encontrado")
    
    except Exception as e:
        st.error(f"❌ Erro ao carregar chamados: {str(e)}")
