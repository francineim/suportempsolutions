# app/chamados.py - VERSÃO FINAL COMPLETA
import streamlit as st
import sys
import os
from datetime import datetime

# Garantir que app está no path
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

try:
    import database
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
        finalizar_chamado_cliente
    )
    import utils
    from utils import (
        validar_arquivo,
        gerar_nome_arquivo_seguro,
        formatar_tempo,
        badge_status,
        badge_prioridade,
        formatar_data_br,
        sanitizar_texto
    )
except ImportError as e:
    st.error(f"Erro ao importar módulos: {e}")
    st.stop()

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
                        
                        # IMPLEMENTAÇÃO 3: Notificar por e-mail
                        try:
                            print(f"\n📧 Tentando enviar e-mail para chamado #{chamado_id}...")
                            from services.chamados_service import notificar_novo_chamado, criar_interacao
                            
                            # Criar interação de abertura
                            criar_interacao(chamado_id, 'cliente', descricao_limpa, 'abertura')
                            print(f"   ✅ Interação criada")
                            
                            # Notificar
                            notificar_novo_chamado(chamado_id)
                            print(f"   ✅ Notificação enviada")
                            
                        except Exception as e:
                            print(f"   ❌ Erro ao enviar e-mail: {e}")
                            import traceback
                            traceback.print_exc()
                        
                        st.success(f"✅ Chamado #{chamado_id} aberto com sucesso!")
                        st.balloons()
                        st.rerun()
                        
                    except Exception as e:
                        st.error(f"❌ Erro: {str(e)}")
    
    st.divider()
    
    # ========== FILTROS ==========
    col_f1, col_f2, col_f3 = st.columns(3)
    
    with col_f1:
        filtro_status = st.selectbox(
            "Status", 
            ["Todos", "Novo", "Em atendimento", "Aguardando Finalização", "Finalizado"]
        )
    
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
            col_s1, col_s2, col_s3, col_s4, col_s5 = st.columns(5)
            col_s1.metric("Total", len(chamados))
            col_s2.metric("Novos", len([c for c in chamados if c['status'] == 'Novo']))
            col_s3.metric("Em Atend.", len([c for c in chamados if c['status'] == 'Em atendimento']))
            col_s4.metric("Aguardando", len([c for c in chamados if c['status'] == 'Aguardando Finalização']))
            col_s5.metric("Finalizados", len([c for c in chamados if c['status'] == 'Finalizado']))
            
            st.divider()
            
            # Lista de chamados
            for ch in chamados:
                status_badge = badge_status(ch['status'])
                prioridade_badge = badge_prioridade(ch['prioridade'])
                
                # Mostrar se foi retornado
                retornos_txt = f" 🔄 ({ch.get('retornos', 0)}x retornado)" if ch.get('retornos', 0) > 0 else ""
                
                titulo = f"{status_badge} #{ch['id']} - {ch['assunto']} {prioridade_badge}{retornos_txt}"
                
                with st.expander(titulo):
                    col1, col2 = st.columns([2, 1])
                    
                    with col1:
                        st.write(f"**📌 Prioridade:** {prioridade_badge} {ch['prioridade']}")
                        st.write(f"**📊 Status:** {status_badge} {ch['status']}")
                        st.write(f"**👤 Usuário:** {ch['usuario']}")
                        st.write(f"**📅 Abertura:** {formatar_data_br(ch['data_abertura'])}")
                        
                        if ch['atendente']:
                            st.write(f"**👨‍💼 Atendente:** {ch['atendente']}")
                        
                        if ch.get('retornos', 0) > 0:
                            st.write(f"**🔄 Retornos:** {ch['retornos']}x")
                    
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
                            
                            # Tempo ATUAL
                            tempo_atual = ch.get("tempo_atendimento_segundos", 0) or 0
                            
                            if ch.get('status_atendimento') == "em_andamento" and ch.get('ultima_retomada'):
                                try:
                                    ultima_retomada_str = str(ch['ultima_retomada']).split('.')[0]
                                    ultima_retomada = datetime.strptime(ultima_retomada_str, "%Y-%m-%d %H:%M:%S")
                                    tempo_decorrido = int((datetime.now() - ultima_retomada).total_seconds())
                                    tempo_atual += tempo_decorrido
                                except:
                                    pass
                            
                            # Exibir tempo
                            st.markdown(f"### ⏱️ {formatar_tempo(tempo_atual)}")
                            
                            # Botões
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
                            
                            # Botão de concluir
                            if st.button(f"✅ Concluir", key=f"concluir_admin_{ch['id']}", type="primary"):
                                st.session_state[f'mostrar_conclusao_{ch["id"]}'] = True
                            
                            # IMPLEMENTAÇÃO 1: Formulário de conclusão
                            if st.session_state.get(f'mostrar_conclusao_{ch["id"]}', False):
                                with st.form(key=f"form_conclusao_{ch['id']}"):
                                    st.write("**📝 Mensagem de Conclusão**")
                                    mensagem = st.text_area(
                                        "Mensagem para o cliente",
                                        height=150,
                                        placeholder="Descreva o que foi feito, orientações, etc."
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
                                        
                                        if arquivos_upload:
                                            if not os.path.exists("uploads/conclusoes"):
                                                os.makedirs("uploads/conclusoes")
                                            
                                            for arq in arquivos_upload:
                                                valido, msg_val = validar_arquivo(arq)
                                                if valido:
                                                    nome_seguro = gerar_nome_arquivo_seguro(arq.name)
                                                    caminho = os.path.join("uploads/conclusoes", nome_seguro)
                                                    
                                                    with open(caminho, "wb") as f:
                                                        f.write(arq.getbuffer())
                                                    
                                                    arquivos_salvos.append({
                                                        'nome': arq.name,
                                                        'caminho': caminho
                                                    })
                                        
                                        sucesso, msg_resultado = concluir_atendimento_admin(
                                            ch['id'], 
                                            mensagem if mensagem else None,
                                            arquivos_salvos if arquivos_salvos else None
                                        )
                                        
                                        if sucesso:
                                            # IMPLEMENTAÇÃO 4: Notificar cliente
                                            try:
                                                print(f"\n📧 Tentando enviar e-mail de conclusão para chamado #{ch['id']}...")
                                                from services.chamados_service import notificar_chamado_concluido
                                                notificar_chamado_concluido(ch['id'], mensagem)
                                                print(f"   ✅ E-mail de conclusão enviado")
                                            except Exception as e:
                                                print(f"   ❌ Erro ao enviar e-mail: {e}")
                                                import traceback
                                                traceback.print_exc()
                                            
                                            st.success(msg_resultado)
                                            del st.session_state[f'mostrar_conclusao_{ch["id"]}']
                                            st.rerun()
                                        else:
                                            st.error(msg_resultado)
                                    
                                    if cancelar:
                                        del st.session_state[f'mostrar_conclusao_{ch["id"]}']
                                        st.rerun()
                        
                        # ========== CLIENTE: Concluir próprio chamado ==========
                        if perfil != "admin" and ch['usuario'] == usuario and ch['status'] == "Em atendimento":
                            if st.button(f"✅ Resolvido", key=f"concluir_cliente_{ch['id']}", type="primary"):
                                sucesso, mensagem = cliente_concluir_chamado(ch['id'], usuario)
                                if sucesso:
                                    st.success(mensagem)
                                    st.rerun()
                                else:
                                    st.error(mensagem)
                    
                    # Descrição
                    st.divider()
                    st.write("**📋 Descrição:**")
                    descricao_completa = buscar_descricao_chamado(ch['id'])
                    st.text_area("", value=descricao_completa, height=100, disabled=True, key=f"desc_{ch['id']}")
                    
                    # Mensagem de conclusão (se existir)
                    if ch['status'] in ['Aguardando Finalização', 'Finalizado']:
                        from database import buscar_mensagem_conclusao
                        msg_conclusao = buscar_mensagem_conclusao(ch['id'])
                        
                        if msg_conclusao:
                            st.divider()
                            st.write("**✅ Mensagem de Conclusão:**")
                            
                            with st.container():
                                st.info(f"**Atendente:** {msg_conclusao['atendente']}")
                                st.write(msg_conclusao['mensagem'])
                                st.caption(f"Enviado em: {formatar_data_br(msg_conclusao['data_envio'])}")
                    
                    # IMPLEMENTAÇÃO 5: Sistema de Interações
                    st.divider()
                    st.write("**💬 Histórico de Interações:**")
                    
                    interacoes = buscar_interacoes_chamado(ch['id'])
                    
                    if interacoes:
                        for inter in interacoes:
                            autor_emoji = "👤" if inter['autor'] == 'cliente' else "👨‍💼"
                            tipo_badge = {
                                'abertura': '🆕',
                                'resposta': '💬',
                                'conclusao': '✅',
                                'retorno': '🔄'
                            }.get(inter.get('tipo', 'resposta'), '💬')
                            
                            with st.container():
                                st.markdown(f"{autor_emoji} {tipo_badge} **{inter['autor'].title()}** - {formatar_data_br(inter['data'])}")
                                st.write(inter['mensagem'])
                                st.caption("---")
                    
                    # Adicionar nova interação (se não estiver finalizado)
                    if ch['status'] not in ['Finalizado']:
                        st.divider()
                        st.write("**💬 Adicionar Mensagem:**")
                        
                        with st.form(key=f"form_interacao_{ch['id']}"):
                            nova_mensagem = st.text_area("Sua mensagem", key=f"msg_{ch['id']}")
                            
                            if st.form_submit_button("📤 Enviar"):
                                if nova_mensagem:
                                    autor_tipo = 'cliente' if perfil != 'admin' else 'atendente'
                                    sucesso, msg = adicionar_interacao_chamado(ch['id'], autor_tipo, nova_mensagem)
                                    
                                    if sucesso:
                                        st.success("Mensagem enviada!")
                                        st.rerun()
                                    else:
                                        st.error(msg)
                    
                    # BOTÕES PARA CLIENTE: Retornar ou Finalizar (apenas se Aguardando Finalização)
                    if ch['status'] == 'Aguardando Finalização' and ch['usuario'] == usuario and perfil != 'admin':
                        st.divider()
                        
                        # Criar 2 colunas para os botões
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
                                            st.rerun()
                                        else:
                                            st.error(msg)
                        
                        with col_btn2:
                            st.write("**✅ Finalizar Chamado**")
                            
                            # Checkbox FORA do form para atualizar em tempo real
                            confirmar = st.checkbox(
                                "✅ Confirmo que foi resolvido",
                                key=f"confirm_finalizar_{ch['id']}"
                            )
                            
                            with st.form(key=f"form_finalizar_{ch['id']}"):
                                st.success("Use se o problema FOI resolvido.")
                                
                                st.write("")  # Espaçamento
                                
                                # Botão sempre habilitado, validação na submissão
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
                                            st.balloons()
                                            st.rerun()
                                        else:
                                            st.error(msg)
                    
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
                                            label="⬇️",
                                            data=f.read(),
                                            file_name=anexo['nome_arquivo'],
                                            key=f"dl_{anexo['id']}"
                                        )
                    else:
                        st.info("Sem anexos")
    
    except Exception as e:
        st.error(f"❌ Erro: {str(e)}")
        import traceback
        st.code(traceback.format_exc())
