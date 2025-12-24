import streamlit as st
from database import (
    conectar, salvar_anexo, buscar_anexos, excluir_anexo,
    excluir_chamado, atualizar_status_chamado, buscar_chamados,
    buscar_descricao_chamado
)
import os
import uuid


def tela_chamados(usuario, perfil):
    """Tela principal de chamados com todas as funcionalidades."""
    
    # ========== NOVO CHAMADO ==========
    st.subheader("📝 Novo Chamado")
    
    with st.expander("➕ Abrir Novo Chamado", expanded=False):
        with st.form("form_novo_chamado", clear_on_submit=True):
            # 5. CORREÇÃO: Garantir que a descrição será salva
            assunto = st.text_input("Assunto *", help="Título breve do problema")
            prioridade = st.selectbox("Prioridade *", ["Baixa", "Média", "Alta", "Urgente"])
            descricao = st.text_area(
                "Descrição Detalhada *", 
                height=150,
                help="Descreva o problema com o máximo de detalhes possível",
                placeholder="Exemplo: Meu computador não liga desde ontem à noite. A tela fica preta e o ventilador faz barulho por alguns segundos antes de desligar. Já tentei trocar o cabo de energia e a tomada..."
            )
            
            # 6. UPLOAD DE ARQUIVO NA ABERTURA
            st.write("📎 **Anexar Arquivo (Opcional):**")
            arquivo_anexo = st.file_uploader(
                "Selecione um arquivo",
                type=['pdf', 'doc', 'docx', 'xls', 'xlsx', 'txt', 'jpg', 'png', 'jpeg'],
                key="novo_chamado_anexo",
                help="Formatos permitidos: PDF, Word, Excel, TXT, Imagens (JPG, PNG)"
            )
            
            submitted = st.form_submit_button("📤 Abrir Chamado", type="primary")
            
            if submitted:
                if assunto and descricao:
                    try:
                        conn = conectar()
                        cursor = conn.cursor()
                        
                        # CORREÇÃO: Inserir descrição corretamente
                        cursor.execute("""
                            INSERT INTO chamados (assunto, prioridade, descricao, status, usuario)
                            VALUES (?, ?, ?, 'Novo', ?)
                        """, (assunto, prioridade, descricao, usuario))
                        
                        conn.commit()
                        chamado_id = cursor.lastrowid
                        
                        # Salvar anexo se houver
                        if arquivo_anexo is not None:
                            # Gerar nome único para o arquivo
                            file_extension = os.path.splitext(arquivo_anexo.name)[1]
                            unique_filename = f"{uuid.uuid4()}{file_extension}"
                            file_path = os.path.join("uploads", unique_filename)
                            
                            # Salvar arquivo
                            with open(file_path, "wb") as f:
                                f.write(arquivo_anexo.getbuffer())
                            
                            # Salvar no banco
                            salvar_anexo(chamado_id, arquivo_anexo.name, file_path)
                        
                        conn.close()
                        
                        st.success(f"✅ Chamado #{chamado_id} aberto com sucesso!")
                        if arquivo_anexo:
                            st.success(f"📎 Arquivo '{arquivo_anexo.name}' anexado!")
                        st.rerun()
                        
                    except Exception as e:
                        st.error(f"❌ Erro ao abrir chamado: {str(e)}")
                else:
                    st.error("⚠️ Por favor, preencha o assunto e a descrição")
    
    st.divider()
    
    # ========== LISTA DE CHAMADOS ==========
    # 1. FILTRAGEM POR PERFIL
    if perfil == "admin":
        st.subheader("📋 Todos os Chamados (Admin)")
    else:
        st.subheader("📋 Meus Chamados")
    
    try:
        # 1. Buscar chamados baseado no perfil
        chamados = buscar_chamados(usuario, perfil)
        
        if not chamados:
            st.info("📭 Nenhum chamado encontrado")
        else:
            # Contadores por status
            total = len(chamados)
            novos = len([c for c in chamados if c["status"] == "Novo"])
            atendimento = len([c for c in chamados if c["status"] == "Em atendimento"])
            concluidos = len([c for c in chamados if c["status"] == "Concluído"])
            
            col1, col2, col3, col4 = st.columns(4)
            col1.metric("Total", total)
            col2.metric("Novos", novos, delta=f"+{novos}" if novos > 0 else None)
            col3.metric("Em Atendimento", atendimento)
            col4.metric("Concluídos", concluidos)
            
            st.divider()
            
            # Lista detalhada de chamados
            for ch in chamados:
                # Cores baseadas no status
                status_color = {
                    "Novo": "🔴",
                    "Em atendimento": "🟡",
                    "Concluído": "🟢"
                }
                
                with st.expander(f"{status_color.get(ch['status'], '⚪')} #{ch['id']} - {ch['assunto']} - Status: {ch['status']}"):
                    col_a, col_b = st.columns([2, 1])
                    
                    with col_a:
                        st.write(f"**Prioridade:** {ch['prioridade']}")
                        st.write(f"**Status:** {ch['status']}")
                        st.write(f"**Usuário:** {ch['usuario']}")
                        st.write(f"**Data Abertura:** {ch['data_abertura']}")
                        
                        if ch['atendente']:
                            st.write(f"**Atendente:** {ch['atendente']}")
                    
                    with col_b:
                        # BOTÕES DE AÇÃO
                        
                        # 2. BOTÃO DE EXCLUSÃO (apenas admin)
                        if perfil == "admin":
                            if st.button(f"🗑️ Excluir", key=f"del_{ch['id']}", type="secondary"):
                                if excluir_chamado(ch['id']):
                                    st.success(f"Chamado #{ch['id']} excluído!")
                                    st.rerun()
                        
                        # 3. BOTÃO PARA ASSUMIR ATENDIMENTO (apenas admin, apenas se status = Novo)
                        if perfil == "admin" and ch['status'] == "Novo":
                            if st.button(f"👨‍💼 Assumir Atendimento", key=f"assumir_{ch['id']}"):
                                if atualizar_status_chamado(ch['id'], "Em atendimento", usuario):
                                    st.success(f"Chamado #{ch['id']} em atendimento!")
                                    st.rerun()
                        
                        # 4. BOTÃO PARA FINALIZAR CHAMADO
                        # Disponível para: admin OU usuário dono do chamado, se status = Em atendimento
                        if ch['status'] == "Em atendimento" and (
                            perfil == "admin" or ch['usuario'] == usuario
                        ):
                            if st.button(f"✅ Finalizar", key=f"finalizar_{ch['id']}"):
                                if atualizar_status_chamado(ch['id'], "Concluído"):
                                    st.success(f"Chamado #{ch['id']} finalizado!")
                                    st.rerun()
                    
                    # Descrição do chamado (CORREÇÃO)
                    st.divider()
                    st.write("**📋 Descrição do Problema:**")
                    
                    # Buscar descrição completa usando função do database
                    descricao_completa = buscar_descricao_chamado(ch['id'])
                    st.write(descricao_completa)
                    
                    # 6. SEÇÃO DE ANEXOS
                    st.divider()
                    st.write("**📎 Anexos:**")
                    
                    # Listar anexos existentes
                    anexos = buscar_anexos(ch['id'])
                    
                    if anexos:
                        for anexo in anexos:
                            col_file1, col_file2, col_file3, col_file4 = st.columns([3, 1, 1, 1])
                            
                            with col_file1:
                                # Ícone baseado no tipo de arquivo
                                file_icon = "📄"
                                if anexo['nome_arquivo'].lower().endswith(('.jpg', '.jpeg', '.png')):
                                    file_icon = "🖼️"
                                elif anexo['nome_arquivo'].lower().endswith('.pdf'):
                                    file_icon = "📕"
                                
                                st.write(f"{file_icon} {anexo['nome_arquivo']}")
                                st.caption(f"Upload: {anexo['data_upload']}")
                            
                            with col_file2:
                                # Botão para visualizar/download
                                if os.path.exists(anexo['caminho_arquivo']):
                                    with open(anexo['caminho_arquivo'], 'rb') as f:
                                        st.download_button(
                                            label="⬇️",
                                            data=f.read(),
                                            file_name=anexo['nome_arquivo'],
                                            key=f"download_{anexo['id']}",
                                            help="Download do arquivo"
                                        )
                            
                            with col_file3:
                                # Visualizar imagem
                                if anexo['nome_arquivo'].lower().endswith(('.png', '.jpg', '.jpeg')):
                                    if st.button("👁️", key=f"view_{anexo['id']}", help="Visualizar imagem"):
                                        st.image(anexo['caminho_arquivo'], caption=anexo['nome_arquivo'])
                            
                            with col_file4:
                                # Excluir anexo (apenas admin ou dono do chamado)
                                if perfil == "admin" or ch['usuario'] == usuario:
                                    if st.button("❌", key=f"del_anexo_{anexo['id']}", help="Excluir anexo"):
                                        if excluir_anexo(anexo['id']):
                                            st.success("Anexo excluído!")
                                            st.rerun()
                    else:
                        st.info("Nenhum arquivo anexado")
                    
                    # 6. ADICIONAR NOVO ANEXO (durante atendimento)
                    st.divider()
                    
                    # Verificar se pode adicionar anexo
                    pode_adicionar = (
                        perfil == "admin" or 
                        ch['usuario'] == usuario or
                        (perfil == "suporte" and ch['status'] == "Em atendimento")
                    )
                    
                    if pode_adicionar:
                        st.write("**➕ Adicionar Novo Anexo:**")
                        
                        novo_arquivo = st.file_uploader(
                            f"Selecione arquivo para anexar",
                            type=['pdf', 'doc', 'docx', 'xls', 'xlsx', 'txt', 'jpg', 'png', 'jpeg'],
                            key=f"upload_{ch['id']}"
                        )
                        
                        col_btn1, col_btn2 = st.columns(2)
                        
                        with col_btn1:
                            if novo_arquivo and st.button(f"📎 Anexar Arquivo", key=f"btn_upload_{ch['id']}", type="primary"):
                                # Gerar nome único
                                file_extension = os.path.splitext(novo_arquivo.name)[1]
                                unique_filename = f"{uuid.uuid4()}{file_extension}"
                                file_path = os.path.join("uploads", unique_filename)
                                
                                # Salvar arquivo
                                with open(file_path, "wb") as f:
                                    f.write(novo_arquivo.getbuffer())
                                
                                # Salvar no banco
                                if salvar_anexo(ch['id'], novo_arquivo.name, file_path):
                                    st.success(f"Arquivo '{novo_arquivo.name}' anexado!")
                                    st.rerun()
                        
                        with col_btn2:
                            # Botão para adicionar comentário (opcional)
                            if st.button("💬 Adicionar Comentário", key=f"coment_{ch['id']}", type="secondary"):
                                st.info("Funcionalidade de comentários em desenvolvimento")
    
    except Exception as e:
        st.error(f"❌ Erro ao carregar chamados: {str(e)}")
        import traceback
        st.code(traceback.format_exc())
