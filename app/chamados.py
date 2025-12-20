import streamlit as st
from database import conectar


def tela_chamados(usuario):
    st.subheader("Chamados")

    conn = conectar()
    cursor = conn.cursor()

    with st.expander("➕ Novo chamado"):
        assunto = st.text_input("Assunto")
        prioridade = st.selectbox(
            "Prioridade",
            ["Muito Alta", "Alta", "Baixa"]
        )
        descricao = st.text_area("Descrição do problema")

        if st.button("Abrir chamado"):
            cursor.execute("""
                INSERT INTO chamados
                (assunto, prioridade, descricao, status, usuario)
                VALUES (?, ?, ?, 'Novo', ?)
            """, (assunto, prioridade, descricao, usuario))
            conn.commit()
            st.success("Chamado aberto com sucesso")
            st.experimental_rerun()

    st.divider()

    st.subheader("Meus chamados")

    cursor.execute("""
        SELECT id, assunto, prioridade, status, data_abertura
        FROM chamados
        WHERE usuario = ?
        ORDER BY data_abertura DESC
    """, (usuario,))

    chamados = cursor.fetchall()
    conn.close()

    for ch in chamados:
        with st.expander(f"#{ch['id']} - {ch['assunto']}"):
            st.write(f"📌 Prioridade: {ch['prioridade']}")
            st.write(f"📍 Status: {ch['status']}")
            st.write(f"📅 Abertura: {ch['data_abertura']}")
