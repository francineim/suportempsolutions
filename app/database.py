def salvar_anexo(chamado_id, nome_arquivo, caminho_arquivo):
    """Salva um anexo no banco de dados."""
    try:
        conn = conectar()
        cursor = conn.cursor()
        
        cursor.execute(
            "INSERT INTO anexos (chamado_id, nome_arquivo, caminho_arquivo) VALUES (?, ?, ?)",
            (chamado_id, nome_arquivo, caminho_arquivo)
        )
        
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print(f"Erro ao salvar anexo: {e}")
        return False
