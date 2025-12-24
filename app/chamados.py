# app/chamados.py
import streamlit as st
from database import (
    conectar, 
    buscar_chamados,
    buscar_descricao_chamado,
    iniciar_atendimento_admin,
    pausar_atendimento,
    retomar_atendimento,
    concluir_atendimento_admin,
    cliente_concluir_chamado,
    obter_tempo_atendimento,
    salvar_anexo,
    buscar_anexos,
    excluir_anexo
)
from utils import (
    validar_arquivo,
    gerar_nome_arquivo_seguro,
    formatar_tempo,
    badge_status,
    badge_prioridade,
    formatar_data_br,
    sanitizar_texto,
    registrar_log
)
import os

def tela_chamados(usuario, perfil):
    """Tela principal de gerenciamento de chamados."""
    st.subheader("📋 Meus Chamados" if perfil != "admin" else "📋 Todos os Chamados")
    
    # ========== NOVO CHAMADO ==========
    with st.expander("➕ Abrir Novo Chamado", expanded=False):
        with st.form("form_novo_chamado", clear_on_submit=True):
            assunto = st.text_input("Assunto *", max_chars=200)
            
            col1, col2 = st.columns(2)
            with col1:
                prioridade = st.selectbox("Prioridade *", ["Baixa", "Média", "Alta", "Urgente"])
            with col2:
                st.write("")  # Espaçamento
            
            descricao = st.text_area(
                "Descrição do problema *", 
                max_chars=2000,
                help="Descreva o problema com o máximo de detalhes possível"
            )
            
            # Upload de arquivo (opcional)
            arquivo = st.file_uploader(
                "Anexar arquivo (opcional)",
                type=['pdf', 'doc', 'docx', 'txt', 'xlsx', 'xls', 'jpg', 'jpeg', 'png', 'gif', 'zip', 'rar'],
                help="Tamanho máximo: 10 MB"
            )
            
            st.markdown("**Campos marcados com * são obrigatórios**")
            
            submitted = st.form_submit_button("📤 Abrir Chamado", type="primary")
            
            if submitted:
                if not assunto or not descricao:
                    st.error("⚠️ Preencha o assunto e a descrição")
                else:
                    # Sanitizar textos
                    assunto_limpo = sanitizar_texto(assunto)
                    descricao_limpa = sanitizar_texto(descricao)
                    
                    try:
                        conn = conectar()
                        cursor = conn.cursor()
                        
                        cursor.execute("""
                            INSERT INTO chamados
                            (assunto, prioridade, descricao, status, usuario)
                            VALUES (?, ?, ?, 'Novo', ?)
                        """, (assunto_limpo, prioridade, descricao_limpa, usuario))
                        
                        conn.commit()
                        chamado_id = cursor.lastrowid
                        conn.close()
                        
                        # Processar arquivo se fornecido
                        if arquivo is not None:
                            valido, msg = validar_arquivo(arquivo)
                            
                            if valido:
                                # Criar pasta uploads se não existir
                                if not os.path.exists("uploads"):
                                    os.makedirs("uploads")
                                
                                # Salvar arquivo com nome seguro
                                nome_seguro = gerar_nome_arquivo_seguro(arquivo.name)
                                caminho = os.path.join("uploads", nome_seguro)
                                
                                with open(caminho, "wb") as f:
                                    f.write(arquivo.getbuffer())
                                
                                # Salvar no banco
                                salvar_anexo(chamado_id, arquivo.name, caminho)
                                st.success(f"✅ Arquivo '{arquivo.name}' anexado com sucesso!")
                            else:
                                st.warning(f"⚠️ Arquivo não anexado: {msg}")
                        
                        # Registrar no log
                        registrar_log(
                            "CHAMADO_ABERTO",
                            usuario,
                            f"Abriu chamado #{chamado_id}: {assunto_limpo}"
                        )
                        
                        st.success(f"✅ Chamado #{chamado_id} aberto com sucesso!")
                        st.balloons()
                        st.rerun()
                        
                    except Exception as e:
                        st.error(f"❌ Erro ao abrir chamado: {str(e)}")
    
    st.divider()
    
    # ========== FILTROS ==========
    col_f1, col_f2, col_f3 = st.columns(3)
    
    with col_f1:
        filtro_status = st.selectbox(
            "Status",
            ["Todos", "Novo", "Em atendimento", "Concluído"]
        )
    
    with col_f2:
        filtro_prioridade = st.selectbox(
            "Prioridade",
            ["Todas", "Urgente", "Alta", "Média", "Baixa"]
        )
    
    with col_f3:
        if perfil == "admin":
            filtro_usuario = st.text_input("Filtrar por usuário")
        else:
            filtro_usuario = None
    
    # ========== LISTA DE CHAMADOS ==========
    try:
        chamados = buscar_chamados(usuario, perfil)
        
        # Aplicar filtros
        if filtro_status != "Todos":
            chamados = [ch for ch in chamados if ch['status'] == filtro_status]
        
        if filtro_prioridade != "Todas":
            chamados = [ch for ch in chamados if ch['prioridade'] == filtro_prioridade]
        
        if filtro_usuario:
            chamados = [ch for ch in chamados if filtro_usuario.lower() in ch['usuario'].lower()]
        
        if not chamados:
            st.info("📭 Nenhum chamado encontrado com os filtros selecionados")
        else:
            # Estatísticas rápidas
            col_s1, col_s2, col_s3, col_s4 = st.columns(4)
            col_s1.metric("Total", len(chamados))
            col_s2.metric("Novos", len([c for c in chamados if c['status'] == 'Novo']))
            col_s3.metric("Em Atend.", len([c for c in chamados if c['status'] == 'Em atendimento']))
            col_s4.metric("Concluídos", len([c for c in chamados if c['status'] == 'Concluído']))
            
            st.divider()
            
            # Lista de chamados
            for ch in chamados:
                status_badge = badge_status(ch['status'])
                prioridade_badge = badge_prioridade(ch['prioridade'])
                
                titulo = f"{status_badge} #{ch['id']} - {ch['assunto']} {prioridade_badge}"
                
                with st.expander(titulo):
                    col1, col2 = st.columns([2, 1])
                    
                    with col1:
                        st.write(f"**📌 Prioridade:** {prioridade_badge} {ch['prioridade']}")
                        st.write(f"**📊 Status:** {status_badge} {ch['status']}")
                        st.write(f"**👤 Usuário:** {ch['usuario']}")
                        st.write(f"**📅 Abertura:** {formatar_data_br(ch['data_abertura'])}")
                        
                        if ch['atendente']:
                            st.write(f"**👨‍💼 Atendente:** {ch['atendente']}")
                        
                        if ch['data_fim_atendimento']:
                            st.write(f"**✅ Conclusão:** {formatar_data_br(ch['data_fim_atendimento'])}")
                            if ch['tempo_atendimento_segundos']:
                                st.write(f"**⏱️ Tempo Total:** {formatar_tempo(ch['tempo_atendimento_segundos'])}")
                    
                    with col2:
                        # ========== CONTROLES POR PERFIL ==========
                        
                        # ADMIN: Iniciar atendimento
                        if perfil == "admin" and ch['status'] == "Novo":
                            if st.button(f"🚀 Iniciar Atendimento", key=f"iniciar_{ch['id']}", type="primary"):
                                sucesso, mensagem = iniciar_atendimento_admin(ch['id'], usuario)
                                if sucesso:
                                    st.success(mensagem)
                                    registrar_log("ATENDIMENTO_INICIADO", usuario, f"Iniciou atendimento do chamado #{ch['id']}")
                                    st.rerun()
                                else:
                                    st.error(mensagem)
                        
                        # ADMIN: Controles durante atendimento
                        if perfil == "admin" and ch['status'] == "Em atendimento":
                            st.write("**⏱️ Controles:**")
                            
                            # Pausar/Retomar
                            if ch.get('status_atendimento') == "em_andamento":
                                if st.button(f"⏸️ Pausar", key=f"pausar_{ch['id']}"):
                                    sucesso, mensagem = pausar_atendimento(ch['id'])
                                    if sucesso:
                                        st.success(mensagem)
                                        st.rerun()
                                    else:
                                        st.error(mensagem)
                            
                            elif ch.get('status_atendimento') == "pausado":
                                if st.button(f"▶️ Retomar", key=f"retomar_{ch['id']}"):
                                    sucesso, mensagem = retomar_atendimento(ch['id'])
                                    if sucesso:
                                        st.success(mensagem)
                                        st.rerun()
                                    else:
                                        st.error(mensagem)
                            
                            # Concluir
                            if st.button(f"✅ Concluir", key=f"concluir_admin_{ch['id']}", type="primary"):
                                sucesso, mensagem = concluir_atendimento_admin(ch['id'])
                                if sucesso:
                                    st.success(mensagem)
                                    registrar_log("ATENDIMENTO_CONCLUIDO", usuario, f"Concluiu atendimento do chamado #{ch['id']}")
                                    st.rerun()
                                else:
                                    st.error(mensagem)
                            
                            # Mostrar tempo atual
                            tempo_atual = obter_tempo_atendimento(ch['id'])
                            st.info(f"⏱️ {formatar_tempo(tempo_atual)}")
                        
                        # CLIENTE: Concluir próprio chamado
                        if perfil != "admin" and ch['usuario'] == usuario and ch['status'] == "Em atendimento":
                            if st.button(f"✅ Marcar como Resolvido", key=f"concluir_cliente_{ch['id']}", type="primary"):
                                sucesso, mensagem = cliente_concluir_chamado(ch['id'], usuario)
                                if sucesso:
                                    st.success(mensagem)
                                    registrar_log("CHAMADO_CONCLUIDO", usuario, f"Cliente concluiu chamado #{ch['id']}")
                                    st.rerun()
                                else:
                                    st.error(mensagem)
                    
                    # Descrição do chamado
                    st.divider()
                    st.write("**📋 Descrição:**")
                    descricao_completa = buscar_descricao_chamado(ch['id'])
                    st.text_area(
                        "Detalhes",
                        value=descricao_completa,
                        height=100,
                        disabled=True,
                        key=f"desc_{ch['id']}"
                    )
                    
                    # Anexos
                    st.divider()
                    st.write("**📎 Anexos:**")
                    
                    anexos = buscar_anexos(ch['id'])
                    
                    if anexos:
                        for anexo in anexos:
                            col_a1, col_a2, col_a3 = st.columns([3, 1, 1])
                            
                            with col_a1:
                                st.write(f"📄 {anexo['nome_arquivo']}")
                                st.caption(f"Enviado: {formatar_data_br(anexo['data_upload'])}")
                            
                            with col_a2:
                                if os.path.exists(anexo['caminho_arquivo']):
                                    with open(anexo['caminho_arquivo'], 'rb') as f:
                                        st.download_button(
                                            label="⬇️ Baixar",
                                            data=f.read(),
                                            file_name=anexo['nome_arquivo'],
                                            key=f"dl_{anexo['id']}"
                                        )
                            
                            with col_a3:
                                if perfil == "admin":
                                    if st.button("🗑️", key=f"del_{anexo['id']}", help="Excluir anexo"):
                                        if excluir_anexo(anexo['id']):
                                            st.success("Anexo excluído!")
                                            st.rerun()
                    else:
                        st.info("Nenhum anexo neste chamado")
                    
                    # Adicionar novo anexo (se chamado não estiver concluído)
                    if ch['status'] != 'Concluído':
                        st.divider()
                        novo_anexo = st.file_uploader(
                            "Adicionar novo anexo",
                            key=f"novo_anexo_{ch['id']}",
                            type=['pdf', 'doc', 'docx', 'txt', 'xlsx', 'xls', 'jpg', 'jpeg', 'png', 'gif', 'zip', 'rar']
                        )
                        
                        if novo_anexo:
                            if st.button(f"📤 Enviar Anexo", key=f"enviar_anexo_{ch['id']}"):
                                valido, msg = validar_arquivo(novo_anexo)
                                
                                if valido:
                                    if not os.path.exists("uploads"):
                                        os.makedirs("uploads")
                                    
                                    nome_seguro = gerar_nome_arquivo_seguro(novo_anexo.name)
                                    caminho = os.path.join("uploads", nome_seguro)
                                    
                                    with open(caminho, "wb") as f:
                                        f.write(novo_anexo.getbuffer())
                                    
                                    if salvar_anexo(ch['id'], novo_anexo.name, caminho):
                                        st.success(f"✅ Anexo '{novo_anexo.name}' adicionado!")
                                        registrar_log("ANEXO_ADICIONADO", usuario, f"Adicionou anexo ao chamado #{ch['id']}")
                                        st.rerun()
                                else:
                                    st.error(f"❌ {msg}")
    
    except Exception as e:
        st.error(f"❌ Erro ao carregar chamados: {str(e)}")
        import traceback
        st.code(traceback.format_exc())
