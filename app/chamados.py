import streamlit as st
from database import (
    conectar, 
    buscar_chamados,
    buscar_descricao_chamado,
    iniciar_atendimento,
    pausar_atendimento,
    retomar_atendimento,
    concluir_atendimento_admin,
    cliente_concluir_chamado,
    obter_tempo_atendimento,
    salvar_anexo,
    buscar_anexos
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
                with st.expander(f"#{ch['id']} - {ch['assunto']} - Status: {ch['status']}"):
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
                        
                        # 1. ADMIN: Iniciar atendimento (para chamados Novos)
                        if perfil == "admin" and ch['status'] == "Novo":
                            if st.button(f"👨‍💼 Iniciar Atendimento", key=f"iniciar_{ch['id']}"):
                                if iniciar_atendimento(ch['id'], usuario):
                                    st.success(f"Atendimento iniciado para chamado #{ch['id']}")
                                    st.rerun()
                        
                        # 2. ADMIN: Controles de atendimento (para chamados Em atendimento)
                        if perfil == "admin" and ch['status'] == "Em atendimento":
                            # Verificar se é o atendente atual
                            if ch['atendente'] == usuario:
                                col_btn1, col_btn2, col_btn3 = st.columns(3)
                                
                                with col_btn1:
                                    if st.button(f"⏸️ Pausar", key=f"pausar_{ch['id']}"):
                                        if pausar_atendimento(ch['id']):
                                            st.success(f"Atendimento pausado para chamado #{ch['id']}")
                                            st.rerun()
                                
                                with col_btn2:
                                    if st.button(f"▶️ Retomar", key=f"retomar_{ch['id']}"):
                                        if retomar_atendimento(ch['id']):
                                            st.success(f"Atendimento retomado para chamado #{ch['id']}")
                                            st.rerun()
                                
                                with col_btn3:
                                    if st.button(f"✅ Concluir Atendimento", key=f"concluir_admin_{ch['id']}"):
                                        if concluir_atendimento_admin(ch['id']):
                                            st.success(f"Atendimento concluído para chamado #{ch['id']}")
                                            st.rerun()
                        
                        # 3. CLIENTE: Concluir chamado (apenas para seus chamados em atendimento)
                        if perfil != "admin" and ch['status'] == "Em atendimento" and ch['usuario'] == usuario:
                            if st.button(f"✅ Concluir Chamado", key=f"concluir_cliente_{ch['id']}"):
                                if cliente_concluir_chamado(ch['id']):
                                    st.success(f"Chamado #{ch['id']} concluído!")
                                    st.rerun()
                    
                    # Mostrar tempo de atendimento se aplicável
                    if ch['status'] == "Em atendimento":
                        tempo = obter_tempo_atendimento(ch['id'])
                        st.info(f"⏱️ **Tempo de atendimento:** {tempo}")
                    
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
