import streamlit as st
from pathlib import Path

from database import criar_tabelas
from auth import autenticar, criar_usuario
from chamados import criar_chamado, listar_chamados, atualizar_status

UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)

st.set_page_config(page_title="Help Desk", layout="wide")

criar_tabelas()

# ---------------- LOGIN ----------------
if "usuario" not in st.session_state:
    st.title("🔐 Login")

    usuario = st.text_input("Usuário")
    senha = st.text_input("Senha", type="password")

    if st.button("Entrar"):
        user = autenticar(usuario, senha)
        if user:
            st.session_state.usuario = user[0]
            st.session_state.perfil = user[1]
            st.rerun()
        else:
            st.error("Usuário ou senha inválidos")

    st.divider()
    st.subheader("➕ Criar usuário")

    novo_usuario = st.text_input("Novo usuário")
    nova_senha = st.text_input("Nova senha", type="password")

    if st.button("Cadastrar"):
        criar_usuario(novo_usuario, nova_senha)
        st.success("Usuário criado com sucesso")

    st.stop()

# ---------------- APP ----------------
st.sidebar.success(f"Logado como {st.session_state.usuario}")
st.title("🛠️ Sistema de Help Desk")

# ---------- NOVO CHAMADO ----------
st.subheader("➕ Novo Chamado")

assunto = st.text_input("Assunto")
prioridade = st.selectbox("Prioridade", ["Muito Alta", "Alta", "Baixa"])
descricao = st.text_area("Descrição da demanda")
anexo = st.file_uploader("Anexo")

anexo_nome = None
if anexo:
    anexo_nome = anexo.name
    with open(UPLOAD_DIR / anexo_nome, "wb") as f:
        f.write(anexo.read())

if st.button("Abrir chamado"):
    criar_chamado(
        st.session_state.usuario,
        assunto,
        prioridade,
        descricao,
        anexo_nome
    )
    st.success("Chamado aberto com sucesso")
    st.rerun()

st.divider()

# ---------- LISTAGEM ----------
st.subheader("📋 Chamados")

for c in listar_chamados():
    chamado_id, usuario, assunto, prioridade, descricao, status, anexo = c

    with st.expander(f"🆔 {chamado_id} | {assunto} | {status}"):
        st.write(f"👤 Usuário: {usuario}")
        st.write(f"⚡ Prioridade: {prioridade}")
        st.write(f"📝 Descrição: {descricao}")

        if anexo:
            st.write(f"📎 Anexo: {anexo}")

        novo_status = st.selectbox(
            "Alterar status",
            ["Aberto", "Em atendimento", "Aguardando finalização", "Concluído"],
            index=["Aberto", "Em atendimento", "Aguardando finalização", "Concluído"].index(status),
            key=f"status_{chamado_id}"
        )

        if st.button("Salvar status", key=f"btn_{chamado_id}"):
            atualizar_status(chamado_id, novo_status)
            st.success("Status atualizado")
            st.rerun()
