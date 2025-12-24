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
    formatar_tempo,
    salvar_anexo,
    buscar_anexos,
    excluir_anexo
)
import os
import uuid
from datetime import datetime

def tela_chamados(usuario, perfil):
    st.subheader("Chamados")
    
    # ========== NOVO CHAMADO ==========
    with st.expander("➕ Novo chamado", expanded=False):
        with st.form("form_novo_chamado", clear_on_submit=True):
            assunto = st.text_input("Assunto")
            prioridade = st.selectbox("Prioridade", ["Baixa", "Média", "Alta", "Urgente"])
            descricao = st.text_area("Descrição do problema")
            
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
                        conn.close()
                        
                        st.success(f"✅ Chamado #{chamado_id} aberto com sucesso!")
                        st.rerun()
                        
                    except Exception as e:
                        st.error(f"❌ Erro ao abrir chamado: {str(e)}")
                else:
                    st.error("⚠️ Preencha o assunto e a descrição")
    
    st.divider()
    
    # ========== LISTA DE CHAMADOS ==========
    try:
        chamados = buscar_chamados(usuario, perfil)
        
        if not chamados:
            st.info("📭 Nenhum chamado encontrado")
        else:
            st.write(f"📊 Total de chamados: {len(chamados)}")
            
            for ch in chamados:
                # Cores para status
                status_emoji = {
                    "Novo": "🔴",
                    "Em atendimento": "🟡",
                    "Concluído": "🟢"
                }.get(ch['status'], "⚪")
                
                with st.expander(f"{status_emoji} #{ch['id']} - {ch['assunto']} - Status: {ch['status']}"):
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.write(f"**Prioridade:** {ch['prioridade']}")
                        st.write(f"**Status:** {ch['status']}")
                        st.write(f"**Usuário:** {ch['usuario']}")
                        st.write(f"**Data Abertura:** {ch['data_abertura']}")
                        
                        if ch['atendente']:
                            st.write(f"**Atendente:** {ch['atendente']}")
                    
                    with col2:
                        # ========== ITEM 2: ADMIN INICIAR ATENDIMENTO ==========
                        if perfil == "admin" and ch['status'] == "Novo":
                            if st.button(f"🚀 Iniciar Atendimento", key=f"iniciar_{ch['id']}"):
                                sucesso, mensagem = iniciar_atendimento_admin(ch['id'], usuario)
                                if sucesso:
                                    st.success(mensagem)
                                    st.rerun()
                                else:
                                    st.error(mensagem)
                        
                        # ========== ITEM 4: CONTROLES DE ATENDIMENTO (ADMIN) ==========
                        if perfil == "admin" and ch['status'] == "Em atendimento":
                            st.write("**⏱️ Controles de Atendimento:**")
                            
                            col_btn1, col_btn2, col_btn3 = st.columns(3)
                            
                            with col_btn1:
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
                            
                            with col_btn2:
                                # Botão para concluir atendimento
                                if st.button(f"✅ Concluir Atendimento", key=f"concluir_admin_{ch['id']}"):
                                    sucesso, mensagem = concluir_atendimento_admin(ch['id'])
                                    if sucesso:
                                        st.success(mensagem)
                                        st.rerun()
                                    else:
                                        st.error(mensagem)
                            
                            with col_btn3:
                                # Mostrar tempo atual
                                tempo_atual = obter_tempo_atendimento(ch['id'])
                                st.write(f"⏱️ {formatar_tempo(tempo_atual)}")
                        
                        # ========== ITEM 3: CLIENTE CONCLUIR CHAMADO ==========
                        if perfil != "admin" and ch['usuario'] == usuario and ch['status'] == "Em atendimento":
                            if st.button(f"✅ Concluir Meu Chamado", key=f"concluir_cliente_{ch['id']}"):
                                sucesso, mensagem = cliente_concluir_chamado(ch['id'], usuario)
                                if sucesso:
                                    st.success(mensagem)
                                    st.rerun()
                                else:
                                    st.error(mensagem)
                    
                    # Descrição do chamado
                    st.divider()
                    st.write("**📋 Descrição:**")
                    descricao_completa = buscar_descricao_chamado(ch['id'])
                    st.write(descricao_completa)
                    
                    # Anexos (mantido da versão anterior)
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
