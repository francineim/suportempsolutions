# app/chamados.py (com timer em tempo real)
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
    sanitizar_texto
)
import os
from datetime import datetime

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
                        
                        st.success(f"✅ Chamado #{chamado_id} aberto com sucesso!")
                        st.balloons()
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
                            
                            # Mostrar tempo ATUAL (calculado em tempo real)
                            tempo_atual = ch.get("tempo_atendimento_segundos", 0) or 0
                            
                            # Se está em andamento, somar tempo desde última retomada
                            if ch.get('status_atendimento') == "em_andamento" and ch.get('ultima_retomada'):
                                try:
                                    ultima_retomada = datetime.strptime(ch['ultima_retomada'], "%Y-%m-%d %H:%M:%S")
                                    tempo_decorrido = int((datetime.now() - ultima_retomada).total_seconds())
                                    tempo_atual += tempo_decorrido
                                except:
                                    pass
                            
                            # Exibir tempo com destaque
                            st.markdown(f"### ⏱️ {formatar_tempo(tempo_atual)}")
                            
                            # Botões de controle
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
                                sucesso, mensagem = concluir_atendimento_admin(ch['id'])
                                if sucesso:
                                    st.success(mensagem)
                                    st.rerun()
                                else:
                                    st.error(mensagem)
                        
                        # ========== CLIENTE: Concluir chamado ==========
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
                        st.info("Sem anexos")
    
    except Exception as e:
        st.error(f"❌ Erro: {str(e)}")
        import traceback
        st.code(traceback.format_exc())
