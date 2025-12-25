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
    excluir_anexo,
    retornar_chamado,
    buscar_interacoes_chamado,
    adicionar_interacao_chamado,
    buscar_mensagem_conclusao
)
from utils import (
    validar_arquivo,
    gerar_nome_arquivo_seguro,
    formatar_tempo,
    badge_status,
    badge_prioridade,
    formatar_data_br,
    sanitizar_texto
)
from services.chamados_service import (
    notificar_novo_chamado,
    notificar_chamado_concluido,
    notificar_chamado_retornado,
    criar_interacao
)
import os
from datetime import datetime
import time

def tela_chamados(usuario, perfil):
    """Tela principal de gerenciamento de chamados."""
    st.subheader("📋 Meus Chamados" if perfil != "admin" else "📋 Todos os Chamados")
    
    # ========== NOVO CHAMADO ==========
    with st.expander("➕ Abrir Novo Chamado", expanded=False):
        with st.form("form_novo_chamado", clear_on_submit=True):
            assunto = st.text_input("Assunto *", max_chars=200)
            prioridade = st.selectbox("Prioridade *", ["Baixa", "Média", "Alta", "Urgente"])
            descricao = st.text_area("Descrição do problema *", max_chars=2000)
            
            arquivo = st.file_uploader(
                "Anexar arquivo (opcional)",
                type=['pdf', 'doc', 'docx', 'txt', 'xlsx', 'xls', 'jpg', 'jpeg', 'png', 'gif', 'zip', 'rar'],
                help="Tamanho máximo: 10 MB"
            )
            
            submitted = st.form_submit_button("📤 Abrir Chamado", type="primary")
            
            if submitted:
                if not assunto or not descricao:
                    st.error("⚠️ Preencha o assunto e a descrição")
                else:
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
                        
                        # Salvar anexo se fornecido
                        if arquivo is not None:
                            valido, msg = validar_arquivo(arquivo)
                            if valido:
                                if not os.path.exists("uploads"):
                                    os.makedirs("uploads")
                                
                                nome_seguro = gerar_nome_arquivo_seguro(arquivo.name)
                                caminho = os.path.join("uploads", nome_seguro)
                                
                                with open(caminho, "wb") as f:
                                    f.write(arquivo.getbuffer())
                                
                                salvar_anexo(chamado_id, arquivo.name, caminho)
                                st.success(f"✅ Arquivo anexado!")
                        
                        # Notificar por e-mail
                        try:
                            # Buscar dados completos do chamado
                            conn = conectar()
                            cursor = conn.cursor()
                            cursor.execute("""
                                SELECT c.*, u.email as email_cliente, u.empresa
                                FROM chamados c
                                LEFT JOIN usuarios u ON c.usuario = u.usuario
                                WHERE c.id = ?
                            """, (chamado_id,))
                            chamado_dados = cursor.fetchone()
                            conn.close()
                            
                            if chamado_dados:
                                chamado_dict = dict(chamado_dados)
                                notificar_novo_chamado(chamado_id)
                                st.success("📧 E-mails de notificação enviados!")
                        except Exception as email_error:
                            st.warning(f"✅ Chamado criado, mas erro no envio de e-mails: {email_error}")
                        
                        st.success(f"✅ Chamado #{chamado_id} aberto com sucesso!")
                        st.balloons()
                        time.sleep(2)
                        st.rerun()
                        
                    except Exception as e:
                        st.error(f"❌ Erro: {str(e)}")
    
    st.divider()
    
    # ========== FILTROS ==========
    col_f1, col_f2, col_f3 = st.columns(3)
    
    with col_f1:
        filtro_status = st.selectbox("Status", ["Todos", "Novo", "Em atendimento", "Concluído"])
    
    with col_f2:
        filtro_prioridade = st.selectbox("Prioridade", ["Todas", "Urgente", "Alta", "Média", "Baixa"])
    
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
            st.info("📭 Nenhum chamado encontrado")
        else:
            # Estatísticas
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
                    
                    with col2:
                        # ========== ADMIN: Iniciar atendimento ==========
                        if perfil == "admin" and ch['status'] == "Novo":
                            if st.button(f"🚀 Iniciar", key=f"iniciar_{ch['id']}", type="primary"):
                                sucesso, mensagem = iniciar_atendimento_admin(ch['id'], usuario)
                                if sucesso:
                                    st.success(mensagem)
                                    st.rerun()
                                else:
                                    st.error(mensagem)
                        
                        # ========== ADMIN: Controles durante atendimento ==========
                        if perfil == "admin" and ch['status'] == "Em atendimento":
                            st.write("**⏱️ Controles:**")
                            
                            # Mostrar tempo ATUAL
                            tempo_atual = obter_tempo_atendimento(ch['id'])
                            
                            # Exibir tempo com destaque
                            st.markdown(f"### ⏱️ {formatar_tempo(tempo_atual)}")
                            
                            # Botões de controle
                            conn = conectar()
                            cursor = conn.cursor()
                            cursor.execute("SELECT status_atendimento FROM chamados WHERE id = ?", (ch['id'],))
                            status_atendimento = cursor.fetchone()['status_atendimento']
                            conn.close()
                            
                            col_btn1, col_btn2 = st.columns(2)
                            
                            with col_btn1:
                                if status_atendimento == "em_andamento":
                                    if st.button(f"⏸️ Pausar", key=f"pausar_{ch['id']}"):
                                        sucesso, mensagem = pausar_atendimento(ch['id'])
                                        if sucesso:
                                            st.success(mensagem)
                                            st.rerun()
                                        else:
                                            st.error(mensagem)
                                elif status_atendimento == "pausado":
                                    if st.button(f"▶️ Retomar", key=f"retomar_{ch['id']}"):
                                        sucesso, mensagem = retomar_atendimento(ch['id'])
                                        if sucesso:
                                            st.success(mensagem)
                                            st.rerun()
                                        else:
                                            st.error(mensagem)
                            
                            with col_btn2:
                                if st.button(f"✅ Concluir", key=f"concluir_admin_{ch['id']}", type="primary"):
                                    st.session_state[f'mostrar_conclusao_{ch["id"]}'] = True
                        
                        # ========== CLIENTE: Concluir chamado ==========
                        if perfil != "admin" and ch['usuario'] == usuario and ch['status'] == "Em atendimento":
                            if st.button(f"✅ Resolvido", key=f"concluir_cliente_{ch['id']}", type="primary"):
                                sucesso, mensagem = cliente_concluir_chamado(ch['id'], usuario)
                                if sucesso:
                                    st.success(mensagem)
                                    st.rerun()
                                else:
                                    st.error(mensagem)
                        
                        # ========== CLIENTE: Retornar chamado ==========
                        if perfil != "admin" and ch['usuario'] == usuario and ch['status'] == "Concluído":
                            if st.button(f"🔄 Retornar", key=f"retornar_{ch['id']}"):
                                st.session_state[f'mostrar_retorno_{ch["id"]}'] = True
                    
                    # Descrição
                    st.divider()
                    st.write("**📋 Descrição:**")
                    descricao_completa = buscar_descricao_chamado(ch['id'])
                    st.text_area("", value=descricao_completa, height=100, disabled=True, key=f"desc_{ch['id']}")
                    
                    # ========== INTERAÇÕES ==========
                    st.divider()
                    st.write("**💬 Histórico de Mensagens:**")
                    
                    interacoes = buscar_interacoes_chamado(ch['id'])
                    
                    if interacoes:
                        for interacao in interacoes:
                            autor_nome = "Atendente" if interacao['autor'] == "atendente" else "Cliente"
                            cor = "#e3f2fd" if interacao['autor'] == "atendente" else "#f3e5f5"
                            
                            with st.container():
                                st.markdown(f"""
                                <div style="background-color: {cor}; padding: 10px; border-radius: 5px; margin: 5px 0;">
                                    <strong>{autor_nome}</strong> ({formatar_data_br(interacao['data'])})
                                    <p>{interacao['mensagem']}</p>
                                </div>
                                """, unsafe_allow_html=True)
                    else:
                        st.info("📭 Nenhuma mensagem ainda")
                    
                    # Nova mensagem
                    st.write("**📝 Nova Mensagem:**")
                    nova_mensagem = st.text_area("Digite sua mensagem:", key=f"msg_{ch['id']}")
                    
                    if st.button("📤 Enviar Mensagem", key=f"enviar_msg_{ch['id']}"):
                        if nova_mensagem:
                            autor = "atendente" if perfil in ["admin", "suporte"] else "cliente"
                            sucesso, resultado = adicionar_interacao_chamado(ch['id'], autor, nova_mensagem)
                            
                            if sucesso:
                                st.success("✅ Mensagem enviada!")
                                st.rerun()
                            else:
                                st.error(f"❌ Erro: {resultado}")
                    
                    # Formulário de conclusão (Admin)
                    if st.session_state.get(f'mostrar_conclusao_{ch["id"]}', False):
                        st.divider()
                        st.write("**📝 Concluir Chamado:**")
                        
                        with st.form(key=f"form_conclusao_{ch['id']}"):
                            mensagem_conclusao = st.text_area(
                                "Mensagem para o cliente:",
                                height=150,
                                placeholder="Descreva o que foi feito, orientações ao cliente, etc."
                            )
                            
                            arquivos_upload = st.file_uploader(
                                "Anexar arquivos (opcional)",
                                accept_multiple_files=True,
                                key=f"upload_conclusao_{ch['id']}"
                            )
                            
                            col_btn1, col_btn2 = st.columns(2)
                            
                            with col_btn1:
                                enviar = st.form_submit_button("✅ Concluir", type="primary")
                            
                            with col_btn2:
                                cancelar = st.form_submit_button("❌ Cancelar")
                            
                            if enviar:
                                arquivos_salvos = []
                                
                                # Processar arquivos
                                if arquivos_upload:
                                    if not os.path.exists("uploads/conclusoes"):
                                        os.makedirs("uploads/conclusoes")
                                    
                                    for arq in arquivos_upload:
                                        valido, msg = validar_arquivo(arq)
                                        if valido:
                                            nome_seguro = gerar_nome_arquivo_seguro(arq.name)
                                            caminho = os.path.join("uploads/conclusoes", nome_seguro)
                                            
                                            with open(caminho, "wb") as f:
                                                f.write(arq.getbuffer())
                                            
                                            arquivos_salvos.append({
                                                'nome': arq.name,
                                                'caminho': caminho
                                            })
                                
                                # Concluir chamado
                                sucesso, msg_resultado = concluir_atendimento_admin(
                                    ch['id'], 
                                    mensagem_conclusao if mensagem_conclusao else None,
                                    arquivos_salvos if arquivos_salvos else None
                                )
                                
                                if sucesso:
                                    # Notificar por e-mail
                                    try:
                                        notificar_chamado_concluido(ch['id'], mensagem_conclusao)
                                        st.success("📧 E-mail de conclusão enviado!")
                                    except Exception as email_error:
                                        st.warning(f"✅ Chamado concluído, mas erro no envio de e-mail: {email_error}")
                                    
                                    del st.session_state[f'mostrar_conclusao_{ch["id"]}']
                                    st.rerun()
                                else:
                                    st.error(msg_resultado)
                            
                            if cancelar:
                                del st.session_state[f'mostrar_conclusao_{ch["id"]}']
                                st.rerun()
                    
                    # Formulário de retorno (Cliente)
                    if st.session_state.get(f'mostrar_retorno_{ch["id"]}', False):
                        st.divider()
                        st.write("**🔄 Retornar Chamado:**")
                        
                        with st.form(key=f"form_retorno_{ch['id']}"):
                            motivo_retorno = st.text_area(
                                "Por que você está retornando este chamado?",
                                height=150,
                                placeholder="Descreva o motivo do retorno, o que ainda não está funcionando, etc."
                            )
                            
                            col_btn1, col_btn2 = st.columns(2)
                            
                            with col_btn1:
                                enviar = st.form_submit_button("🔄 Retornar", type="primary")
                            
                            with col_btn2:
                                cancelar = st.form_submit_button("❌ Cancelar")
                            
                            if enviar:
                                if motivo_retorno:
                                    sucesso, resultado = retornar_chamado(ch['id'], usuario, motivo_retorno)
                                    
                                    if sucesso:
                                        # A função retornar_chamado já chama a notificação
                                        st.success("✅ Chamado retornado!")
                                        del st.session_state[f'mostrar_retorno_{ch["id"]}']
                                        st.rerun()
                                    else:
                                        st.error(f"❌ Erro: {resultado}")
                                else:
                                    st.error("⚠️ Digite o motivo do retorno")
                            
                            if cancelar:
                                del st.session_state[f'mostrar_retorno_{ch["id"]}']
                                st.rerun()
                    
                    # Mensagem de conclusão (se existir)
                    if ch['status'] == 'Concluído':
                        msg_conclusao = buscar_mensagem_conclusao(ch['id'])
                        
                        if msg_conclusao:
                            st.divider()
                            st.write("**✅ Mensagem de Conclusão:**")
                            
                            with st.container():
                                st.info(f"**Atendente:** {msg_conclusao['atendente']}")
                                st.write(msg_conclusao['mensagem'])
                                st.caption(f"Enviado em: {formatar_data_br(msg_conclusao['data_envio'])}")
                    
                    # Anexos
                    st.divider()
                    st.write("**📎 Anexos:**")
                    
                    anexos = buscar_anexos(ch['id'])
                    
                    if anexos:
                        for anexo in anexos:
                            col_a1, col_a2 = st.columns([3, 1])
                            
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
                    else:
                        st.info("📭 Nenhum anexo")
        
    except Exception as e:
        st.error(f"❌ Erro: {str(e)}")
        import traceback
        st.code(traceback.format_exc())
