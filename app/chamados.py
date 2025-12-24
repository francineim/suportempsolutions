import streamlit as st
from database import (
    conectar, 
    buscar_chamados,
    buscar_descricao_chamado,
    excluir_chamado,
    atualizar_status_chamado,
    salvar_anexo,
    buscar_anexos,
    excluir_anexo
)
import os
import uuid

def garantir_pasta_uploads():
    """Garante que a pasta uploads existe."""
    uploads_dir = "uploads"
    if not os.path.exists(uploads_dir):
        os.makedirs(uploads_dir, exist_ok=True)
    return uploads_dir

def tela_chamados(usuario, perfil):
    st.subheader("Chamados")
    
    uploads_path = garantir_pasta_uploads()
    
    # ========== NOVO CHAMADO ==========
    with st.expander("➕ Novo chamado", expanded=False):
        # Usar um formulário com estado para controlar o envio
        with st.form(key="form_novo_chamado", clear_on_submit=True):
            assunto = st.text_input("Assunto", placeholder="Ex: Computador não liga")
            prioridade = st.selectbox("Prioridade", ["Baixa", "Média", "Alta", "Urgente"])
            descricao = st.text_area("Descrição do problema", 
                                   placeholder="Descreva detalhadamente o problema...",
                                   height=120)
            
            st.markdown("📎 **Anexar arquivo (opcional):**")
            arquivo = st.file_uploader(
                "Selecione um arquivo",
                type=['pdf', 'doc', 'docx', 'xls', 'xlsx', 'txt', 'jpg', 'png', 'jpeg'],
                key="novo_chamado_file",
                label_visibility="collapsed"
            )
            
            submit_button = st.form_submit_button(label="📤 Abrir chamado", type="primary")
            
            if submit_button:
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
                        
                        # Salvar anexo, se houver
                        if arquivo is not None:
                            # Verificar tamanho do arquivo (limite: 10MB)
                            arquivo.seek(0, os.SEEK_END)
                            tamanho = arquivo.tell()
                            arquivo.seek(0)
                            
                            if tamanho <= 10 * 1024 * 1024:  # 10MB
                                # Gerar nome único
                                file_ext = os.path.splitext(arquivo.name)[1].lower()
                                unique_name = f"chamado_{chamado_id}_{uuid.uuid4()}{file_ext}"
                                file_path = os.path.join(uploads_path, unique_name)
                                
                                # Salvar arquivo
                                with open(file_path, "wb") as f:
                                    f.write(arquivo.getbuffer())
                                
                                # Salvar no banco
                                salvar_anexo(chamado_id, arquivo.name, file_path)
                                st.success(f"✅ Chamado #{chamado_id} aberto com sucesso! Arquivo anexado: {arquivo.name}")
                            else:
                                st.warning(f"✅ Chamado #{chamado_id} aberto com sucesso, mas o arquivo foi ignorado (tamanho superior a 10MB).")
                        else:
                            st.success(f"✅ Chamado #{chamado_id} aberto com sucesso!")
                        
                        # Não usamos st.rerun() aqui, pois o formulário é clear_on_submit
                        # e o sucesso já foi mostrado. O usuário pode continuar vendo a lista.
                        
                    except Exception as e:
                        st.error(f"❌ Erro ao salvar chamado: {str(e)}")
                        if conn:
                            conn.rollback()
                    finally:
                        if conn:
                            conn.close()
                else:
                    st.warning("⚠️ Preencha o assunto e a descrição")
    
    st.divider()
    
    # ========== LISTA DE CHAMADOS ==========
    try:
        chamados = buscar_chamados(usuario, perfil)
        
        if not chamados:
            st.info("📭 Nenhum chamado encontrado")
            return
        
        if perfil == "admin":
            st.subheader(f"Todos os Chamados ({len(chamados)})")
        else:
            st.subheader(f"Meus Chamados ({len(chamados)})")
        
        for ch in chamados:
            status_icon = {"Novo": "🔴", "Em atendimento": "🟡", "Concluído": "🟢"}.get(ch['status'], "⚪")
            
            with st.expander(f"{status_icon} #{ch['id']} - {ch['assunto']} - {ch['usuario']}"):
                col1, col2 = st.columns([2, 1])
                
                with col1:
                    st.write(f"**Prioridade:** {ch['prioridade']}")
                    st.write(f"**Status:** {ch['status']}")
                    st.write(f"**Usuário:** {ch['usuario']}")
                    st.write(f"**Data:** {ch['data_abertura']}")
                    
                    if ch['atendente']:
                        st.write(f"**Atendente:** {ch['atendente']}")
                
                with col2:
                    if perfil == "admin":
                        if st.button(f"🗑️ Excluir", key=f"del_{ch['id']}", type="secondary", use_container_width=True):
                            if excluir_chamado(ch['id']):
                                st.success(f"Chamado #{ch['id']} excluído!")
                                st.rerun()
                    
                    if perfil == "admin" and ch['status'] == "Novo":
                        if st.button(f"👨‍💼 Assumir", key=f"assumir_{ch['id']}", use_container_width=True):
                            if atualizar_status_chamado(ch['id'], "Em atendimento", usuario):
                                st.success(f"Chamado #{ch['id']} em atendimento!")
                                st.rerun()
                    
                    if ch['status'] == "Em atendimento" and (perfil == "admin" or ch['usuario'] == usuario):
                        if st.button(f"✅ Finalizar", key=f"finalizar_{ch['id']}", use_container_width=True):
                            if atualizar_status_chamado(ch['id'], "Concluído"):
                                st.success(f"Chamado #{ch['id']} finalizado!")
                                st.rerun()
                
                st.markdown("---")
                st.write("**📋 Descrição:**")
                descricao_completa = buscar_descricao_chamado(ch['id'])
                st.write(descricao_completa)
                
                st.markdown("---")
                st.write("**📎 Anexos:**")
                
                anexos = buscar_anexos(ch['id'])
                
                if anexos:
                    for anexo in anexos:
                        col_a, col_b = st.columns([3, 1])
                        
                        with col_a:
                            if os.path.exists(anexo['caminho_arquivo']):
                                file_icon = "📄"
                                if anexo['nome_arquivo'].lower().endswith(('.jpg', '.jpeg', '.png')):
                                    file_icon = "🖼️"
                                elif anexo['nome_arquivo'].lower().endswith('.pdf'):
                                    file_icon = "📕"
                                st.write(f"{file_icon} {anexo['nome_arquivo']}")
                                st.caption(f"Adicionado: {anexo['data_upload']}")
                            else:
                                st.warning(f"⚠️ Arquivo não encontrado: {anexo['nome_arquivo']}")
                        
                        with col_b:
                            if os.path.exists(anexo['caminho_arquivo']):
                                with open(anexo['caminho_arquivo'], 'rb') as f:
                                    st.download_button(
                                        label="⬇️ Download",
                                        data=f.read(),
                                        file_name=anexo['nome_arquivo'],
                                        key=f"dl_{anexo['id']}",
                                        use_container_width=True
                                    )
                else:
                    st.info("Nenhum arquivo anexado")
                
                st.markdown("---")
                if perfil == "admin" or ch['usuario'] == usuario:
                    st.write("**➕ Adicionar anexo:**")
                    
                    novo_file = st.file_uploader(
                        "Selecione arquivo",
                        type=['pdf', 'doc', 'docx', 'xls', 'xlsx', 'txt', 'jpg', 'png', 'jpeg'],
                        key=f"up_{ch['id']}"
                    )
                    
                    if novo_file and st.button(f"Anexar ao chamado #{ch['id']}", key=f"btn_{ch['id']}"):
                        garantir_pasta_uploads()
                        
                        novo_file.seek(0, os.SEEK_END)
                        tamanho = novo_file.tell()
                        novo_file.seek(0)
                        
                        if tamanho > 10 * 1024 * 1024:
                            st.warning("⚠️ Arquivo muito grande (máximo 10MB).")
                        else:
                            file_ext = os.path.splitext(novo_file.name)[1].lower()
                            unique_name = f"chamado_{ch['id']}_{uuid.uuid4()}{file_ext}"
                            file_path = os.path.join(uploads_path, unique_name)
                            
                            try:
                                with open(file_path, "wb") as f:
                                    f.write(novo_file.getbuffer())
                                
                                if salvar_anexo(ch['id'], novo_file.name, file_path):
                                    st.success(f"Arquivo '{novo_file.name}' anexado!")
                                    st.rerun()
                            except Exception as file_error:
                                st.error(f"❌ Erro ao salvar arquivo: {file_error}")
    
    except Exception as e:
        st.error(f"❌ Erro ao carregar chamados: {str(e)}")
