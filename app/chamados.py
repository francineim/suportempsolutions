import streamlit as st
from database import conectar


def tela_chamados(usuario):
    st.subheader("Chamados")

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
                        
                        # Verificar se foi salvo
                        conn2 = conectar()
                        cursor2 = conn2.cursor()
                        cursor2.execute("SELECT COUNT(*) as total FROM chamados WHERE id = ?", (chamado_id,))
                        resultado = cursor2.fetchone()
                        conn2.close()
                        
                        st.info(f"🔍 Verificação: Chamado salvo no banco: {'✅ SIM' if resultado['total'] > 0 else '❌ NÃO'}")
                        
                    except Exception as e:
                        st.error(f"❌ Erro ao abrir chamado: {str(e)}")
                        import traceback
                        st.code(traceback.format_exc())
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
            for ch in chamados:
                with st.expander(f"#{ch['id']} - {ch['assunto']}"):
                    st.write(f"📌 Prioridade: {ch['prioridade']}")
                    st.write(f"📍 Status: {ch['status']}")
                    st.write(f"📅 Abertura: {ch['data_abertura']}")
    except Exception as e:
        st.error(f"❌ Erro ao carregar chamados: {str(e)}")
        import traceback
        st.code(traceback.format_exc())
