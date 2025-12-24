import streamlit as st
from database import conectar

def tela_dashboard():
    st.subheader("📊 Dashboard")
    
    # Verificar se há usuário na sessão
    if 'usuario' not in st.session_state or 'perfil' not in st.session_state:
        st.error("⚠️ Por favor, faça login para acessar o dashboard.")
        return
    
    usuario = st.session_state.usuario
    perfil = st.session_state.perfil
    
    conn = conectar()
    cursor = conn.cursor()
    
    try:
        # Filtrar por usuário se não for admin
        if perfil == "admin":
            # Admin vê todos os chamados
            cursor.execute("SELECT COUNT(*) FROM chamados")
            total = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM chamados WHERE status = 'Novo'")
            novos = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM chamados WHERE status = 'Em atendimento'")
            atendimento = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM chamados WHERE status = 'Concluído'")
            concluidos = cursor.fetchone()[0]
        else:
            # Usuário comum vê apenas seus chamados
            cursor.execute("SELECT COUNT(*) FROM chamados WHERE usuario = ?", (usuario,))
            total = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM chamados WHERE usuario = ? AND status = 'Novo'", (usuario,))
            novos = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM chamados WHERE usuario = ? AND status = 'Em atendimento'", (usuario,))
            atendimento = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM chamados WHERE usuario = ? AND status = 'Concluído'", (usuario,))
            concluidos = cursor.fetchone()[0]
        
        conn.close()
        
        # Mostrar métricas
        col1, col2, col3, col4 = st.columns(4)
        
        col1.metric("Total de Chamados", total)
        col2.metric("Novos", novos)
        col3.metric("Em Atendimento", atendimento)
        col4.metric("Concluídos", concluidos)
        
        # Informação sobre o filtro
        if perfil != "admin":
            st.info(f"📌 Mostrando apenas chamados do usuário: **{usuario}**")
        
    except Exception as e:
        st.error(f"❌ Erro ao carregar dashboard: {str(e)}")
        conn.close()
