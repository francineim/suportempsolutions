from database import conectar


def criar_chamado(usuario, assunto, prioridade, descricao, anexo):
    conn = conectar()
    cur = conn.cursor()

    cur.execute("""
        INSERT INTO chamados (
            usuario, assunto, prioridade, descricao, status, anexo
        )
        VALUES (?, ?, ?, ?, 'Aberto', ?)
    """, (usuario, assunto, prioridade, descricao, anexo))

    conn.commit()
    conn.close()


def listar_chamados():
    conn = conectar()
    cur = conn.cursor()

    cur.execute("""
        SELECT id, usuario, assunto, prioridade, descricao, status, anexo
        FROM chamados
        ORDER BY id DESC
    """)

    chamados = cur.fetchall()
    conn.close()
    return chamados


def atualizar_status(chamado_id, novo_status):
    conn = conectar()
    cur = conn.cursor()

    cur.execute(
        "UPDATE chamados SET status=? WHERE id=?",
        (novo_status, chamado_id)
    )

    conn.commit()
    conn.close()

