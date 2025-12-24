    with st.expander("➕ Novo chamado"):
        with st.form("form_novo_chamado", clear_on_submit=True):
            assunto = st.text_input("Assunto")
            prioridade = st.selectbox("Prioridade", ["Baixa", "Média", "Alta", "Urgente"])
            descricao = st.text_area("Descrição do problema")
            
            # Upload de arquivo
            st.write("📎 Anexar arquivo (opcional):")
            arquivo = st.file_uploader(
                "Selecione um arquivo",
                type=['pdf', 'doc', 'docx', 'xls', 'xlsx', 'txt', 'jpg', 'png', 'jpeg'],
                key="novo_chamado_file"
            )
            
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
                        
                        # Salvar anexo se houver
                        if arquivo is not None:
                            # Gerar nome único
                            file_ext = os.path.splitext(arquivo.name)[1]
                            unique_name = f"{uuid.uuid4()}{file_ext}"
                            file_path = os.path.join("uploads", unique_name)
                            
                            # Salvar arquivo
                            with open(file_path, "wb") as f:
                                f.write(arquivo.getbuffer())
                            
                            # Salvar no banco
                            salvar_anexo(chamado_id, arquivo.name, file_path)
                        
                        conn.close()
                        
                        st.success(f"✅ Chamado #{chamado_id} aberto com sucesso!")
                        if arquivo:
                            st.success(f"📎 Arquivo '{arquivo.name}' anexado!")
                        st.experimental_rerun()
                        
                    except Exception as e:
                        st.error(f"❌ Erro ao abrir chamado: {str(e)}")
                        # Se houver erro, fazer rollback se a conexão ainda estiver aberta
                        try:
                            conn.rollback()
                            conn.close()
                        except:
                            pass
                else:
                    st.error("⚠️ Preencha o assunto e a descrição")
