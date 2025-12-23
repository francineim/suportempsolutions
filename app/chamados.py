import streamlit as st  # ADICIONE ESTA LINHA!
from database import conectar


def tela_chamados(usuario):
    st.subheader("Chamados")
    
    # Formulário para novo chamado
    with st.expander("➕ Novo chamado"):
        with st.form("form_novo_chamado", clear_on_submit=True):
            assunto = st.text_input("Assunto")
            prioridade = st.selectbox(
                "Prioridade",
                ["Muito Alta", "Alta", "Baixa"]
            )
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
                        st.rerun()  # Atualiza a página para mostrar o novo chamado
                        
                    except Exception as e:
                        st.error(f"❌ Erro ao abrir chamado: {str(e)}")
                else:
                    st.error("⚠️ Por favor, preencha o assunto e a descrição")

    st.divider()

    st.subheader("Meus chamados")

    try:
        conn = conectar()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT id, assunto, prioridade, status, data_abertura
            FROM chamados
            WHERE usuario = ?
            ORDER BY data_abertura DESC
        """, (usuario,))
        
        chamados = cursor.fetchall()
        conn.close()

        if not chamados:
            st.info("📭 Você ainda não tem chamados abertos")
        else:
            st.write(f"📊 Total de chamados: {len(chamados)}")
            
            # Criar uma tabela visual
            for ch in chamados:
                col1, col2 = st.columns([4, 1])
                with col1:
                    st.write(f"**#{ch['id']}** - {ch['assunto']}")
                    st.write(f"📌 Prioridade: {ch['prioridade']} | 📍 Status: {ch['status']}")
                with col2:
                    st.write(f"📅 {ch['data_abertura']}")
                st.divider()
                
    except Exception as e:
        st.error(f"❌ Erro ao carregar chamados: {str(e)}")
