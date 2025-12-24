import streamlit as st
from database import conectar

def tela_dashboard():
    st.subheader("📊 Dashboard")
    
    conn = conectar()
    cursor = conn.cursor()
    
    cursor.execute("SELECT COUNT(*) FROM chamados")
    total = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM chamados WHERE status = 'Novo'")
    novos = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM chamados WHERE status = 'Em atendimento'")
    atendimento = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM chamados WHERE status = 'Concluído'")
    concluidos = cursor.fetchone()[0]
    
    conn.close()
    
    col1, col2, col3, col4 = st.columns(4)
    
    col1.metric("Total de Chamados", total)
    col2.metric("Novos", novos)
    col3.metric("Em Atendimento", atendimento)
    col4.metric("Concluídos", concluidos)
