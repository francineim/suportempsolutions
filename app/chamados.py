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
                    try:
                        conn = conectar()
                        cursor = conn.cursor()
                        
                        cursor.execute("""
                            INSERT INTO chamados
                            (assunto, prioridade, descricao, status, usuario)
                            VALUES (?, ?, ?, 'Novo', ?)
                        """, (assunto, prioridade, descricao, usuario))
                        
                        conn.commit()
                        chamado_id = cursor.lastrowid
                        
                        # Salvar anexo se houver
                        if arquivo is not None:
                            # Gerar nome único
                            file_ext = os.path.splitext(arquivo.name)[1]
                            unique_name = f"{uuid.uuid4()}{file_ext}"
                            file_path = os.path.join("uploads", unique_name)
                            
                            # Salvar arquivo
                            with open(file_path, "wb") as f:
                                f.write(arquivo.getbuffer())
                            
                            # Salvar no banco
                            salvar_anexo(chamado_id, arquivo.name, file_path)
                        
                        conn.close()
                        
                        st.success(f"✅ Chamado #{chamado_id} aberto com sucesso!")
                        if arquivo:
                            st.success(f"📎 Arquivo '{arquivo.name}' anexado!")
                        st.rerun()
                        
                    except Exception as e:
                        st.error(f"❌ Erro ao abrir chamado: {str(e)}")
                else:
                    st.error("⚠️ Preencha o assunto e a descrição")
    
    st.divider()
    
    # ========== LISTA DE CHAMADOS ==========
    if perfil == "admin":
        st.subheader("Todos os Chamados")
    else:
        st.subheader("Meus Chamados")
    
    try:
        chamados = buscar_chamados(usuario, perfil)
        
        if not chamados:
            st.info("📭 Nenhum chamado encontrado")
        else:
            st.write(f"📊 Total: {len(chamados)}")
            
            for ch in chamados:
                with st.expander(f"#{ch['id']} - {ch['assunto']} - {ch['status']}"):
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.write(f"📌 Prioridade: {ch['prioridade']}")
                        st.write(f"📍 Status: {ch['status']}")
                        st.write(f"👤 Usuário: {ch['usuario']}")
                        st.write(f"📅 Abertura: {ch['data_abertura']}")
                        
                        if ch['atendente']:
                            st.write(f"👨‍💼 Atendente: {ch['atendente']}")
                    
                    with col2:
                        # BOTÕES DE AÇÃO
                        
                        # 2. Excluir chamado (apenas admin)
                        if perfil == "admin":
                            if st.button(f"🗑️ Excluir", key=f"del_{ch['id']}"):
                                if excluir_chamado(ch['id']):
                                    st.success(f"Chamado #{ch['id']} excluído!")
                                    st.rerun()
                        
                        # 3. Assumir atendimento (apenas admin, status Novo)
                        if perfil == "admin" and ch['status'] == "Novo":
                            if st.button(f"👨‍💼 Assumir", key=f"assumir_{ch['id']}"):
                                if atualizar_status_chamado(ch['id'], "Em atendimento", usuario):
                                    st.success(f"Chamado #{ch['id']} em atendimento!")
                                    st.rerun()
                        
                        # 4. Finalizar chamado
                        if ch['status'] == "Em atendimento" and (perfil == "admin" or ch['usuario'] == usuario):
                            if st.button(f"✅ Finalizar", key=f"finalizar_{ch['id']}"):
                                if atualizar_status_chamado(ch['id'], "Concluído"):
                                    st.success(f"Chamado #{ch['id']} finalizado!")
                                    st.rerun()
                    
                    # Descrição do chamado
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
                            col_a, col_b, col_c = st.columns([3, 1, 1])
                            
                            with col_a:
                                st.write(f"📄 {anexo['nome_arquivo']}")
                            
                            with col_b:
                                # Download
                                if os.path.exists(anexo['caminho_arquivo']):
                                    with open(anexo['caminho_arquivo'], 'rb') as f:
                                        st.download_button(
                                            label="⬇️",
                                            data=f.read(),
                                            file_name=anexo['nome_arquivo'],
                                            key=f"dl_{anexo['id']}"
                                        )
                            
                            with col_c:
                                # Excluir (admin ou dono)
                                if perfil == "admin" or ch['usuario'] == usuario:
                                    if st.button("❌", key=f"del_a_{anexo['id']}"):
                                        if excluir_anexo(anexo['id']):
                                            st.success("Anexo excluído!")
                                            st.rerun()
                    else:
                        st.write("Nenhum anexo")
                    
                    # Adicionar novo anexo
                    st.divider()
                    
                    if perfil == "admin" or ch['usuario'] == usuario:
                        st.write("**➕ Adicionar anexo:**")
                        
                        novo_file = st.file_uploader(
                            f"Anexar ao chamado #{ch['id']}",
                            type=['pdf', 'doc', 'docx', 'xls', 'xlsx', 'txt', 'jpg', 'png', 'jpeg'],
                            key=f"up_{ch['id']}"
                        )
                        
                        if novo_file and st.button(f"Anexar", key=f"btn_up_{ch['id']}"):
                            # Salvar arquivo
                            file_ext = os.path.splitext(novo_file.name)[1]
                            unique_name = f"{uuid.uuid4()}{file_ext}"
                            file_path = os.path.join("uploads", unique_name)
                            
                            with open(file_path, "wb") as f:
                                f.write(novo_file.getbuffer())
                            
                            # Salvar no banco
                            if salvar_anexo(ch['id'], novo_file.name, file_path):
                                st.success(f"Arquivo '{novo_file.name}' anexado!")
                                st.rerun()
    
    except Exception as e:
        st.error(f"❌ Erro ao carregar chamados: {str(e)}")
