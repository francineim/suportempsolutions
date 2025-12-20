import streamlit as st
from database import conectar
from contextlib import contextmanager


@contextmanager
def get_db_connection():
    """Context manager para gerenciar conexões de banco de dados"""
    conn = conectar()
    try:
        yield conn
    finally:
        conn.close()


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
                    with get_db_connection() as conn:
                        cursor = conn.cursor()
                        cursor.execute("""
                            INSERT INTO chamados
                            (assunto, prioridade, descricao, status, usuario)
                            VALUES (?, ?, ?, 'Novo', ?)
                        """, (assunto, prioridade, descricao, usuario))
                        conn.commit()
                    st.success("Chamado aberto com sucesso!")
                else:
                    st.error("Por favor, preencha o assunto e a descrição")

    st.divider()

    st.subheader("Meus chamados")

    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, assunto, prioridade, status, data_abertura
            FROM chamados
            WHERE usuario = ?
            ORDER BY data_abertura DESC
        """, (usuario,))
        chamados = cursor.fetchall()

    if not chamados:
        st.info("Você ainda não tem chamados abertos")
    else:
        for ch in chamados:
            with st.expander(f"#{ch['id']} - {ch['assunto']}"):
                st.write(f"📌 Prioridade: {ch['prioridade']}")
                st.write(f"📍 Status: {ch['status']}")
                st.write(f"📅 Abertura: {ch['data_abertura']}")
