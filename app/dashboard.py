import streamlit as st
from database import buscar_estatisticas_usuario

def tela_dashboard():
    st.subheader("📊 Dashboard")
    
    # Obter usuário e perfil da sessão
    usuario = st.session_state.get('usuario')
    perfil = st.session_state.get('perfil')
    
    if not usuario:
        st.error("Usuário não autenticado")
        return
    
    # Buscar estatísticas baseadas no perfil
    estatisticas = buscar_estatisticas_usuario(usuario, perfil)
    
    if perfil == "admin":
        st.info("👑 **Vista de Administrador**: Mostrando estatísticas de TODOS os chamados")
    else:
        st.info(f"👤 **Vista de {usuario}**: Mostrando apenas SEUS chamados")
    
    col1, col2, col3, col4 = st.columns(4)
    
    col1.metric("Total de Chamados", estatisticas["total"])
    col2.metric("Novos", estatisticas["novos"])
    col3.metric("Em Atendimento", estatisticas["em_atendimento"])
    col4.metric("Concluídos", estatisticas["concluidos"])
    
    # Adicionar gráfico de distribuição
    if estatisticas["total"] > 0:
        st.markdown("---")
        st.subheader("📈 Distribuição por Status")
        
        import pandas as pd
        import matplotlib.pyplot as plt
        
        data = {
            'Status': ['Novos', 'Em Atendimento', 'Concluídos'],
            'Quantidade': [estatisticas["novos"], estatisticas["em_atendimento"], estatisticas["concluidos"]]
        }
        
        df = pd.DataFrame(data)
        
        # Criar gráfico de barras
        fig, ax = plt.subplots()
        ax.bar(df['Status'], df['Quantidade'], color=['red', 'orange', 'green'])
        ax.set_ylabel('Quantidade')
        ax.set_title('Distribuição de Chamados')
        
        # Adicionar valores nas barras
        for i, v in enumerate(df['Quantidade']):
            ax.text(i, v + 0.1, str(v), ha='center')
        
        st.pyplot(fig)
    
    # Para admin, mostrar mais detalhes
    if perfil == "admin" and estatisticas["em_atendimento"] > 0:
        st.markdown("---")
        st.subheader("⏱️ Chamados em Atendimento Ativo")
        
        from database import conectar, formatar_tempo
        
        conn = conectar()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, assunto, usuario, atendente, tempo_atendimento_segundos, 
                   status_atendimento, ultima_retomada
            FROM chamados 
            WHERE status = 'Em atendimento'
            ORDER BY ultima_retomada DESC
        """)
        
        chamados_atendimento = cursor.fetchall()
        conn.close()
        
        for ch in chamados_atendimento:
            tempo_formatado = formatar_tempo(ch["tempo_atendimento_segundos"])
            status_emoji = "⏸️" if ch["status_atendimento"] == "pausado" else "▶️"
            
            st.write(f"{status_emoji} **#{ch['id']}** - {ch['assunto']}")
            st.write(f"   👤 Usuário: {ch['usuario']} | 👨‍💼 Atendente: {ch['atendente']}")
            st.write(f"   ⏱️ Tempo: {tempo_formatado}")
            st.write("---")
