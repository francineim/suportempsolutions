# app/chamados.py
"""
Tela de Gerenciamento de Chamados
"""

import streamlit as st
import os
from datetime import datetime

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
    finalizar_chamado_cliente,
    buscar_mensagem_conclusao,
    buscar_anexos_interacao,
    retornar_chamado_admin,
    criar_chamado,
    registrar_download
)

from utils import formatar_tempo, badge_status, badge_prioridade, agora_brasilia_str

def formatar_data_br(data):
    """Formata data para padrão brasileiro DD/MM/YYYY HH:MM"""
    if data is None:
        return "N/A"
    
    if isinstance(data, str):
        try:
            data = datetime.fromisoformat(data.replace('Z', '+00:00'))
        except:
            try:
                data = datetime.strptime(data.split('.')[0], "%Y-%m-%d %H:%M:%S")
            except:
                return data
    
    if isinstance(data, datetime):
        return data.strftime('%d/%m/%Y %H:%M')
    
    return str(data)


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
                    from utils import sanitizar_texto, validar_arquivo, gerar_nome_arquivo_seguro
                    
                    assunto_limpo = sanitizar_texto(assunto)
                    descricao_limpa = sanitizar_texto(descricao)
                    
                    try:
                        # Criar chamado
                        chamado_id = criar_chamado(assunto_limpo, prioridade, descricao_limpa, usuario)
                        
                        if chamado_id:
                            # Processar anexo se houver
                            if arquivo is not None:
                                valido, msg = validar_arquivo(arquivo)
                                if valido:
                                    if not os.path.exists("uploads"):
                                        os.makedirs("uploads")
                                    
                                    nome_seguro = gerar_nome_arquivo_seguro(arquivo.name)
                                    caminho = os.path.join("uploads", nome_seguro)
                                    
                                    with open(caminho, "wb") as f:
                                        f.write(arquivo.getbuffer())
                                    
                                    salvar_anexo(chamado_id, arquivo.name, caminho, arquivo.size)
                                    st.success(f"✅ Arquivo anexado!")
                            
                            # Enviar notificações por e-mail
                            try:
                                print(f"\n📧 Tentando enviar e-mail para chamado #{chamado_id}...")
                                from services.chamados_service import notificar_novo_chamado, criar_interacao
                                
                                criar_interacao(chamado_id, 'cliente', descricao_limpa, 'abertura')
                                print(f"   ✅ Interação criada")
                                
                                notificar_novo_chamado(chamado_id)
                                print(f"   ✅ Notificação enviada")
                                
                            except Exception as e:
                                print(f"   ❌ Erro ao enviar e-mail: {e}")
                                import traceback
                                traceback.print_exc()
                            
                            st.success(f"✅ Chamado #{chamado_id} aberto com sucesso!")
                            st.balloons()
                            st.rerun()
                        else:
                            st.error("❌ Erro ao criar chamado")
                        
                    except Exception as e:
                        st.error(f"❌ Erro: {str(e)}")
    
    st.divider()
    
    # ========== FILTROS ==========
    col_f1, col_f2, col_f3 = st.columns(3)
    
    with col_f1:
        filtro_status = st.selectbox(
            "Status", 
            ["Todos", "Novo", "Em atendimento", "Aguardando Finalização", "Aguardando Cliente", "Finalizado"],
            key="filtro_status_chamados"
        )
    
    with col_f2:
        filtro_prioridade = st.selectbox(
            "Prioridade", 
            ["Todas", "Urgente", "Alta", "Média", "Baixa"],
            key="filtro_prioridade_chamados"
        )
    
    with col_f3:
        if perfil == "admin":
            filtro_usuario = st.text_input("Filtrar por usuário", key="filtro_usuario_chamados")
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
            st.caption(f"📊 Total: {len(chamados)} chamado(s)")
            
            # Exibir chamados
            for ch in chamados:
                status_badge = badge_status(ch['status'])
                prioridade_badge = badge_prioridade(ch['prioridade'])
                
                # Título do expander
                titulo = f"{status_badge} {prioridade_badge} **#{ch['id']}** - {ch['assunto'][:50]}..."
                
                with st.expander(titulo, expanded=False):
                    # Info do chamado
                    col1, col2, col3 = st.columns(3)
                    
                    with col1:
                        st.write(f"**ID:** #{ch['id']}")
                        st.write(f"**Status:** {ch['status']}")
                        st.write(f"**Prioridade:** {ch['prioridade']}")
                    
                    with col2:
                        st.write(f"**Usuário:** {ch['usuario']}")
                        st.write(f"**Atendente:** {ch.get('atendente', 'N/A')}")
                        st.write(f"**Retornos:** {ch.get('retornos', 0)}")
                    
                    with col3:
                        st.write(f"**Abertura:** {formatar_data_br(ch['data_abertura'])}")
                        st.write(f"**Tempo:** {formatar_tempo(obter_tempo_atendimento(ch['id']))}")
                        if ch.get('data_fim_atendimento'):
                            st.write(f"**Conclusão:** {formatar_data_br(ch['data_fim_atendimento'])}")
                    
                    st.divider()
                    
                    # Descrição
                    st.write("**📝 Descrição:**")
                    descricao = buscar_descricao_chamado(ch['id'])
                    st.text_area("", value=descricao, disabled=True, height=100, key=f"desc_{ch['id']}", label_visibility="collapsed")
                    
                    # ========== AÇÕES DO ADMIN ==========
                    if perfil == "admin":
                        st.divider()
                        st.write("**🔧 Ações do Atendente:**")
                        
                        col_a1, col_a2, col_a3, col_a4 = st.columns(4)
                        
                        # Iniciar atendimento
                        if ch['status'] == 'Novo':
                            with col_a1:
                                if st.button("▶️ Iniciar", key=f"iniciar_{ch['id']}", use_container_width=True):
                                    sucesso, msg = iniciar_atendimento_admin(ch['id'], usuario)
                                    if sucesso:
                                        st.success(msg)
                                        
                                        # Criar interação
                                        try:
                                            from services.chamados_service import criar_interacao
                                            criar_interacao(ch['id'], 'atendente', 'Atendimento iniciado', 'inicio')
                                        except:
                                            pass
                                        
                                        st.rerun()
                                    else:
                                        st.error(msg)
                        
                        # Pausar/Retomar
                        if ch['status'] == 'Em atendimento':
                            with col_a1:
                                if ch.get('status_atendimento') == 'em_andamento':
                                    if st.button("⏸️ Pausar", key=f"pausar_{ch['id']}", use_container_width=True):
                                        sucesso, msg = pausar_atendimento(ch['id'])
                                        if sucesso:
                                            st.success(msg)
                                            st.rerun()
                                        else:
                                            st.error(msg)
                                else:
                                    if st.button("▶️ Retomar", key=f"retomar_{ch['id']}", use_container_width=True):
                                        sucesso, msg = retomar_atendimento(ch['id'])
                                        if sucesso:
                                            st.success(msg)
                                            st.rerun()
                                        else:
                                            st.error(msg)
                            
                            # Concluir
                            with col_a2:
                                with st.popover("✅ Concluir"):
                                    st.write("**Mensagem de conclusão:**")
                                    msg_conclusao = st.text_area(
                                        "Mensagem",
                                        placeholder="Descreva o que foi feito...",
                                        key=f"msg_conclusao_{ch['id']}",
                                        label_visibility="collapsed"
                                    )
                                    
                                    # Anexo de conclusão
                                    arquivo_conclusao = st.file_uploader(
                                        "Anexar arquivo",
                                        key=f"anexo_conclusao_{ch['id']}",
                                        type=['pdf', 'doc', 'docx', 'txt', 'xlsx', 'xls', 'jpg', 'jpeg', 'png']
                                    )
                                    
                                    if st.button("✅ Confirmar Conclusão", key=f"confirmar_conclusao_{ch['id']}", type="primary"):
                                        # Processar anexo
                                        arquivos_conclusao = None
                                        if arquivo_conclusao:
                                            from utils import gerar_nome_arquivo_seguro
                                            if not os.path.exists("uploads"):
                                                os.makedirs("uploads")
                                            nome_seguro = gerar_nome_arquivo_seguro(arquivo_conclusao.name)
                                            caminho = os.path.join("uploads", nome_seguro)
                                            with open(caminho, "wb") as f:
                                                f.write(arquivo_conclusao.getbuffer())
                                            arquivos_conclusao = [{'nome': arquivo_conclusao.name, 'caminho': caminho}]
                                        
                                        sucesso, msg = concluir_atendimento_admin(ch['id'], msg_conclusao, arquivos_conclusao)
                                        if sucesso:
                                            st.success(msg)
                                            
                                            # Notificar cliente
                                            try:
                                                from services.chamados_service import notificar_chamado_concluido
                                                notificar_chamado_concluido(ch['id'], msg_conclusao)
                                            except:
                                                pass
                                            
                                            st.rerun()
                                        else:
                                            st.error(msg)
                            
                            # Retornar ao cliente
                            with col_a3:
                                with st.popover("🔄 Retornar"):
                                    st.write("**Retornar ao cliente:**")
                                    msg_retorno_admin = st.text_area(
                                        "Mensagem",
                                        placeholder="Informe o que precisa do cliente...",
                                        key=f"msg_retorno_admin_{ch['id']}",
                                        label_visibility="collapsed"
                                    )
                                    
                                    # Anexo de retorno
                                    arquivo_retorno = st.file_uploader(
                                        "Anexar arquivo",
                                        key=f"anexo_retorno_{ch['id']}",
                                        type=['pdf', 'doc', 'docx', 'txt', 'xlsx', 'xls', 'jpg', 'jpeg', 'png']
                                    )
                                    
                                    if st.button("🔄 Enviar para Cliente", key=f"enviar_retorno_{ch['id']}"):
                                        if not msg_retorno_admin:
                                            st.error("Informe o motivo do retorno")
                                        else:
                                            # Processar anexo
                                            arquivos = None
                                            if arquivo_retorno:
                                                from utils import gerar_nome_arquivo_seguro
                                                if not os.path.exists("uploads"):
                                                    os.makedirs("uploads")
                                                nome_seguro = gerar_nome_arquivo_seguro(arquivo_retorno.name)
                                                caminho = os.path.join("uploads", nome_seguro)
                                                with open(caminho, "wb") as f:
                                                    f.write(arquivo_retorno.getbuffer())
                                                arquivos = [{'nome': arquivo_retorno.name, 'caminho': caminho}]
                                            
                                            sucesso, msg = retornar_chamado_admin(ch['id'], usuario, msg_retorno_admin, arquivos)
                                            if sucesso:
                                                st.success(msg)
                                                
                                                # Notificar cliente
                                                try:
                                                    from services.chamados_service import notificar_retorno_admin
                                                    notificar_retorno_admin(ch['id'], msg_retorno_admin)
                                                except:
                                                    pass
                                                
                                                st.rerun()
                                            else:
                                                st.error(msg)
                    
                    # ========== INTERAÇÕES ==========
                    st.divider()
                    st.write("**💬 Histórico de Interações:**")
                    
                    interacoes = buscar_interacoes_chamado(ch['id'])
                    
                    if interacoes:
                        for inter in interacoes:
                            autor_icon = "👤" if inter['autor'] == 'cliente' else "🛠️"
                            autor_nome = "Cliente" if inter['autor'] == 'cliente' else "Atendente"
                            
                            st.markdown(f"""
                            <div style='background: {"#e3f2fd" if inter["autor"] == "atendente" else "#f5f5f5"}; 
                                        padding: 10px; margin: 5px 0; border-radius: 8px;
                                        border-left: 3px solid {"#1976d2" if inter["autor"] == "atendente" else "#9e9e9e"};'>
                                <strong>{autor_icon} {autor_nome}</strong> - <small>{formatar_data_br(inter['data'])}</small>
                                <p style='margin: 5px 0 0 0;'>{inter['mensagem']}</p>
                            </div>
                            """, unsafe_allow_html=True)
                            
                            # Anexos da interação
                            anexos_inter = buscar_anexos_interacao(inter['id'])
                            if anexos_inter:
                                for anexo in anexos_inter:
                                    if os.path.exists(anexo['caminho_arquivo']):
                                        with open(anexo['caminho_arquivo'], 'rb') as f:
                                            st.download_button(
                                                f"📎 {anexo['nome_arquivo']}",
                                                f.read(),
                                                anexo['nome_arquivo'],
                                                key=f"dl_inter_{inter['id']}_{anexo['id']}"
                                            )
                    else:
                        st.info("Sem interações registradas")
                    
                    # Nova mensagem
                    if ch['status'] not in ['Finalizado', 'Cancelado']:
                        with st.form(key=f"form_msg_{ch['id']}"):
                            nova_mensagem = st.text_area(
                                "Nova mensagem",
                                placeholder="Digite sua mensagem...",
                                key=f"nova_msg_{ch['id']}"
                            )
                            
                            if st.form_submit_button("📤 Enviar Mensagem"):
                                if nova_mensagem:
                                    autor_tipo = 'cliente' if perfil != 'admin' else 'atendente'
                                    sucesso, msg = adicionar_interacao_chamado(ch['id'], autor_tipo, nova_mensagem)
                                    
                                    if sucesso:
                                        st.success("Mensagem enviada!")
                                        
                                        # Notificar
                                        try:
                                            from services.chamados_service import criar_interacao
                                            # Já foi criada acima, só precisa notificar
                                        except:
                                            pass
                                        
                                        st.rerun()
                                    else:
                                        st.error(msg)
                    
                    # ========== AÇÕES DO CLIENTE ==========
                    if ch['status'] == 'Aguardando Finalização' and ch['usuario'] == usuario and perfil != 'admin':
                        st.divider()
                        
                        # Mensagem de conclusão
                        msg_conclusao = buscar_mensagem_conclusao(ch['id'])
                        if msg_conclusao:
                            st.info(f"**Mensagem do Atendente:** {msg_conclusao.get('mensagem', '')}")
                        
                        col_btn1, col_btn2 = st.columns(2)
                        
                        with col_btn1:
                            st.write("**🔄 Retornar Chamado**")
                            
                            with st.form(key=f"form_retorno_{ch['id']}"):
                                st.warning("Use se o problema NÃO foi resolvido.")
                                
                                mensagem_retorno = st.text_area(
                                    "Por que está retornando?",
                                    placeholder="Explique o motivo...",
                                    height=100,
                                    key=f"txt_retorno_{ch['id']}"
                                )
                                
                                if st.form_submit_button("🔙 Retornar", type="secondary", use_container_width=True):
                                    if not mensagem_retorno:
                                        st.error("Explique o motivo do retorno")
                                    else:
                                        sucesso, msg = retornar_chamado(ch['id'], usuario, mensagem_retorno)
                                        
                                        if sucesso:
                                            st.success(msg)
                                            
                                            # Notificar
                                            try:
                                                from services.chamados_service import notificar_chamado_retornado
                                                notificar_chamado_retornado(ch['id'], mensagem_retorno)
                                            except:
                                                pass
                                            
                                            st.rerun()
                                        else:
                                            st.error(msg)
                        
                        with col_btn2:
                            st.write("**✅ Finalizar Chamado**")
                            
                            confirmar = st.checkbox(
                                "✅ Confirmo que foi resolvido",
                                key=f"confirm_finalizar_{ch['id']}"
                            )
                            
                            with st.form(key=f"form_finalizar_{ch['id']}"):
                                st.success("Use se o problema FOI resolvido.")
                                
                                submit_finalizar = st.form_submit_button(
                                    "✅ Finalizar Definitivamente", 
                                    type="primary", 
                                    use_container_width=True
                                )
                                
                                if submit_finalizar:
                                    if not confirmar:
                                        st.error("⚠️ Você precisa confirmar que o problema foi resolvido!")
                                    else:
                                        sucesso, msg = finalizar_chamado_cliente(ch['id'], usuario)
                                        
                                        if sucesso:
                                            st.success(msg)
                                            
                                            # Notificar
                                            try:
                                                from services.chamados_service import notificar_chamado_finalizado
                                                notificar_chamado_finalizado(ch['id'])
                                            except:
                                                pass
                                            
                                            st.balloons()
                                            st.rerun()
                                        else:
                                            st.error(msg)
                    
                    # ========== ANEXOS ==========
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
                                        dados = f.read()
                                        if st.download_button(
                                            label="⬇️",
                                            data=dados,
                                            file_name=anexo['nome_arquivo'],
                                            key=f"dl_{anexo['id']}"
                                        ):
                                            registrar_download(usuario, anexo['nome_arquivo'], anexo['caminho_arquivo'], ch['id'])
                    else:
                        st.info("Sem anexos")
    
    except Exception as e:
        st.error(f"❌ Erro: {str(e)}")
        import traceback
        st.code(traceback.format_exc())
