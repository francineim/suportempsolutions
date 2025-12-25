# app/dashboard.py
import streamlit as st
from database import buscar_estatisticas_usuario, conectar
from utils import formatar_tempo
from datetime import datetime

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
    
    # Adicionar gráfico SIMPLES
    if estatisticas["total"] > 0:
        st.markdown("---")
        st.subheader("📈 Distribuição por Status")
        
        import pandas as pd
        
        data = {
            'Status': ['Novos', 'Em Atendimento', 'Concluídos'],
            'Quantidade': [estatisticas["novos"], estatisticas["em_atendimento"], estatisticas["concluidos"]]
        }
        
        df = pd.DataFrame(data)
        st.dataframe(df, hide_index=True, use_container_width=True)
        
        chart_data = pd.DataFrame({
            'Quantidade': [estatisticas["novos"], estatisticas["em_atendimento"], estatisticas["concluidos"]]
        }, index=['Novos', 'Em Atendimento', 'Concluídos'])
        
        st.bar_chart(chart_data)
    
    # Para admin, mostrar chamados em atendimento COM ATUALIZAÇÃO EM TEMPO REAL
    if perfil == "admin" and estatisticas["em_atendimento"] > 0:
        st.markdown("---")
        st.subheader("⏱️ Chamados em Atendimento Ativo")
        
        # Container para atualização automática
        placeholder = st.empty()
        
        # Botão para atualizar manualmente
        col_btn1, col_btn2 = st.columns([1, 5])
        with col_btn1:
            if st.button("🔄 Atualizar"):
                st.rerun()
        with col_btn2:
            st.caption("Atualize para ver o tempo mais recente")
        
        with placeholder.container():
            conn = conectar()
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, assunto, usuario, atendente, tempo_atendimento_segundos, 
                       status_atendimento, ultima_retomada
                FROM chamados 
                WHERE status = 'Em atendimento'
                ORDER BY 
                    CASE WHEN status_atendimento = 'em_andamento' THEN 1 ELSE 2 END,
                    ultima_retomada DESC
            """)
            
            chamados_atendimento = cursor.fetchall()
            conn.close()
            
            if not chamados_atendimento:
                st.info("Nenhum chamado em atendimento no momento")
            else:
                for ch in chamados_atendimento:
                    tempo_atual = ch["tempo_atendimento_segundos"] or 0
                    
                    # Se está em andamento, calcular tempo decorrido desde última retomada
                    if ch["status_atendimento"] == "em_andamento" and ch["ultima_retomada"]:
                        try:
                            # Remover microsegundos do timestamp
                            ultima_retomada_str = str(ch["ultima_retomada"]).split('.')[0]
                            ultima_retomada = datetime.strptime(ultima_retomada_str, "%Y-%m-%d %H:%M:%S")
                            tempo_decorrido = int((datetime.now() - ultima_retomada).total_seconds())
                            tempo_atual += tempo_decorrido
                        except Exception as e:
                            st.caption(f"Aviso: {e}")
                    
                    tempo_formatado = formatar_tempo(tempo_atual)
                    status_emoji = "⏸️" if ch["status_atendimento"] == "pausado" else "▶️"
                    
                    # Card para cada chamado
                    with st.container():
                        col_a, col_b = st.columns([3, 1])
                        
                        with col_a:
                            st.write(f"{status_emoji} **#{ch['id']}** - {ch['assunto']}")
                            st.caption(f"👤 Cliente: {ch['usuario']} | 👨‍💼 Atendente: {ch['atendente'] or 'Não atribuído'}")
                        
                        with col_b:
                            # Destacar tempo se estiver rodando
                            if ch["status_atendimento"] == "em_andamento":
                                st.markdown(f"### ⏱️ {tempo_formatado}")
                            else:
                                st.write(f"⏱️ {tempo_formatado}")
                        
                        st.divider()
