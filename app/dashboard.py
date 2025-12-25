# app/dashboard.py
import streamlit as st
from database import buscar_estatisticas_usuario, conectar, obter_tempo_atendimento
from utils import formatar_tempo

def tela_dashboard():
    st.subheader("📊 Dashboard")
    
    usuario = st.session_state.get('usuario')
    perfil = st.session_state.get('perfil')
    
    if not usuario:
        st.error("Usuário não autenticado")
        return
    
    estatisticas = buscar_estatisticas_usuario(usuario, perfil)
    
    if perfil == "admin":
        st.info("👑 Vista de Administrador - Todos os chamados")
    else:
        st.info(f"👤 Vista de {usuario} - Seus chamados")
    
    col1, col2, col3, col4 = st.columns(4)
    
    col1.metric("Total", estatisticas["total"])
    col2.metric("Novos", estatisticas["novos"])
    col3.metric("Em Atendimento", estatisticas["em_atendimento"])
    col4.metric("Concluídos", estatisticas["concluidos"])
    
    if estatisticas["total"] > 0:
        st.markdown("---")
        st.subheader("📈 Distribuição")
        
        import pandas as pd
        
        chart_data = pd.DataFrame({
            'Quantidade': [estatisticas["novos"], estatisticas["em_atendimento"], estatisticas["concluidos"]]
        }, index=['Novos', 'Em Atendimento', 'Concluídos'])
        
        st.bar_chart(chart_data)
    
    if perfil == "admin" and estatisticas["em_atendimento"] > 0:
        st.markdown("---")
        st.subheader("⏱️ Chamados em Atendimento")
        
        if st.button("🔄 Atualizar Tempos"):
            st.rerun()
        
        try:
            conn = conectar()
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, assunto, usuario, atendente, status_atendimento
                FROM chamados 
                WHERE status = 'Em atendimento'
                ORDER BY id DESC
            """)
            
            chamados = cursor.fetchall()
            conn.close()
            
            for ch in chamados:
                tempo = obter_tempo_atendimento(ch['id'])
                status_emoji = "⏸️" if ch['status_atendimento'] == "pausado" else "▶️"
                
                col_a, col_b = st.columns([3, 1])
                
                with col_a:
                    st.write(f"{status_emoji} **#{ch['id']}** - {ch['assunto']}")
                    st.caption(f"Cliente: {ch['usuario']} | Atendente: {ch['atendente']}")
                
                with col_b:
                    if ch['status_atendimento'] == 'em_andamento':
                        st.markdown(f"### {formatar_tempo(tempo)}")
                    else:
                        st.write(formatar_tempo(tempo))
                
                st.divider()
        except Exception as e:
            st.error(f"Erro: {e}")
