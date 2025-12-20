from app.database import conectar


def autenticar(usuario, senha):
    conn = conectar()
    cur = conn.cursor()

    cur.execute(
        "SELECT usuario, perfil FROM usuarios WHERE usuario=? AND senha=?",
        (usuario, senha)
    )

    user = cur.fetchone()
    conn.close()
    return user


def criar_usuario(usuario, senha, perfil="cliente"):
    conn = conectar()
    cur = conn.cursor()

    cur.execute(
        "INSERT INTO usuarios (usuario, senha, perfil) VALUES (?, ?, ?)",
        (usuario, senha, perfil)
    )

    conn.commit()
    conn.close()
