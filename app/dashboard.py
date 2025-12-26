# app/dashboard.py
import streamlit as st
from database import (
    buscar_estatisticas_usuario, 
    conectar, 
    obter_tempo_atendimento,
    buscar_estatisticas_por_empresa,
    buscar_chamados_com_tempo,
    formatar_tempo  # Importar do database para evitar circular import
)

def tela_dashboard():
    st.subheader("📊 Dashboard")
    
    usuario = st.session_state.get('usuario')
    perfil = st.session_state.get('perfil')
    
    if not usuario:
        st.error("Usuário não autenticado")
        return
    
    estatisticas = buscar_estatisticas_usuario(usuario, perfil)
    
    # IMPLEMENTAÇÃO 5: Texto simplificado
    if perfil != "admin":
        st.info("📊 Seus Chamados")
    
    col1, col2, col3, col4, col5 = st.columns(5)
    
    col1.metric("Total", estatisticas["total"])
    col2.metric("Novos", estatisticas["novos"])
    col3.metric("Em Atendimento", estatisticas["em_atendimento"])
    
    # Contar aguardando finalização e finalizados
    try:
        conn = conectar()
        cursor = conn.cursor()
        if perfil == "admin":
            cursor.execute("SELECT COUNT(*) as aguardando FROM chamados WHERE status = 'Aguardando Finalização'")
            aguardando = cursor.fetchone()['aguardando']
            cursor.execute("SELECT COUNT(*) as finalizados FROM chamados WHERE status = 'Finalizado'")
            finalizados = cursor.fetchone()['finalizados']
        else:
            cursor.execute("SELECT COUNT(*) as aguardando FROM chamados WHERE usuario = ? AND status = 'Aguardando Finalização'", (usuario,))
            aguardando = cursor.fetchone()['aguardando']
            cursor.execute("SELECT COUNT(*) as finalizados FROM chamados WHERE usuario = ? AND status = 'Finalizado'", (usuario,))
            finalizados = cursor.fetchone()['finalizados']
        conn.close()
        
        col4.metric("Aguardando", aguardando)
        col5.metric("Finalizados", finalizados)
    except Exception as e:
        col4.metric("Aguardando", 0)
        col5.metric("Finalizados", 0)
        print(f"Erro ao buscar contadores: {e}")
    
    if estatisticas["total"] > 0:
        st.markdown("---")
        st.subheader("📈 Distribuição")
        
        import pandas as pd
        
        # Gráfico simplificado
        try:
            chart_data = pd.DataFrame({
                'Quantidade': [
                    estatisticas["novos"], 
                    estatisticas["em_atendimento"], 
                    estatisticas.get("concluidos", 0)
                ]
            }, index=['Novos', 'Em Atendimento', 'Aguardando/Finalizados'])
            
            st.bar_chart(chart_data)
        except Exception as e:
            print(f"Erro ao criar gráfico: {e}")
    
    # IMPLEMENTAÇÃO 2: Estatísticas avançadas para ADMIN
    if perfil == "admin":
        st.markdown("---")
        
        # Abas para diferentes visualizações
        tab1, tab2, tab3 = st.tabs(["📊 Por Empresa", "🎫 Por Chamado", "⏱️ Chamados em Andamento"])
        
        # TAB 1: Estatísticas por Empresa
        with tab1:
            st.subheader("📊 Estatísticas por Empresa")
            
            try:
                empresas = buscar_estatisticas_por_empresa()
                
                if empresas:
                    for emp in empresas:
                        with st.expander(f"🏢 {emp.get('empresa') or 'Sem empresa'}"):
                            col_e1, col_e2, col_e3, col_e4 = st.columns(4)
                            
                            col_e1.metric("Total", emp.get('total_chamados', 0))
                            col_e2.metric("Novos", emp.get('novos', 0))
                            col_e3.metric("Em Atend.", emp.get('em_atendimento', 0))
                            col_e4.metric("Concluídos", emp.get('concluidos', 0))
                            
                            if emp.get('tempo_medio'):
                                st.write(f"**⏱️ Tempo Médio:** {formatar_tempo(int(emp['tempo_medio']))}")
                else:
                    st.info("📭 Nenhuma estatística disponível")
            except Exception as e:
                st.error(f"Erro ao carregar estatísticas por empresa: {e}")
        
        # TAB 2: Estatísticas por Chamado
        with tab2:
            st.subheader("🎫 Chamados Concluídos - Tempo de Atendimento")
            
            try:
                chamados = buscar_chamados_com_tempo()
                
                if chamados:
                    # Criar DataFrame
                    import pandas as pd
                    df_chamados = pd.DataFrame([
                        {
                            'ID': f"#{ch['id']}",
                            'Assunto': ch['assunto'][:30] + '...' if len(ch['assunto']) > 30 else ch['assunto'],
                            'Cliente': ch['usuario'],
                            'Empresa': ch.get('empresa') or 'N/A',
                            'Atendente': ch.get('atendente') or 'N/A',
                            'Tempo': formatar_tempo(ch.get('tempo_atendimento_segundos', 0)),
                            'Abertura': ch.get('data_abertura', '')[:10] if ch.get('data_abertura') else 'N/A'
                        }
                        for ch in chamados
                    ])
                    
                    st.dataframe(df_chamados, use_container_width=True, hide_index=True)
                    
                    # Estatísticas gerais
                    st.divider()
                    
                    col_s1, col_s2, col_s3 = st.columns(3)
                    
                    tempos = [ch.get('tempo_atendimento_segundos', 0) for ch in chamados if ch.get('tempo_atendimento_segundos')]
                    tempo_medio = sum(tempos) / len(tempos) if tempos else 0
                    tempo_min = min(tempos) if tempos else 0
                    tempo_max = max(tempos) if tempos else 0
                    
                    col_s1.metric("⏱️ Tempo Médio", formatar_tempo(int(tempo_medio)))
                    col_s2.metric("🏃 Mais Rápido", formatar_tempo(tempo_min))
                    col_s3.metric("🐌 Mais Lento", formatar_tempo(tempo_max))
                else:
                    st.info("📭 Nenhum chamado concluído ainda")
            except Exception as e:
                st.error(f"Erro ao carregar chamados: {e}")
        
        # TAB 3: Chamados em Andamento (original)
        with tab3:
            st.subheader("⏱️ Chamados em Atendimento")
            
            try:
                # Buscar chamados em atendimento
                conn = conectar()
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT COUNT(*) as total FROM chamados WHERE status = 'Em atendimento'
                """)
                total_atendimento = cursor.fetchone()['total']
                conn.close()
                
                if total_atendimento > 0:
                    if st.button("🔄 Atualizar Tempos"):
                        st.rerun()
                    
                    conn = conectar()
                    cursor = conn.cursor()
                    cursor.execute("""
                        SELECT c.id, c.assunto, c.usuario, u.empresa, c.atendente, c.status_atendimento
                        FROM chamados c
                        LEFT JOIN usuarios u ON c.usuario = u.usuario
                        WHERE c.status = 'Em atendimento'
                        ORDER BY c.id DESC
                    """)
                    
                    chamados = cursor.fetchall()
                    conn.close()
                    
                    for ch in chamados:
                        tempo = obter_tempo_atendimento(ch['id'])
                        status_emoji = "⏸️" if ch.get('status_atendimento') == "pausado" else "▶️"
                        
                        col_a, col_b = st.columns([3, 1])
                        
                        with col_a:
                            st.write(f"{status_emoji} **#{ch['id']}** - {ch['assunto']}")
                            empresa_txt = f" ({ch.get('empresa', '')})" if ch.get('empresa') else ""
                            st.caption(f"Cliente: {ch['usuario']}{empresa_txt} | Atendente: {ch.get('atendente', 'N/A')}")
                        
                        with col_b:
                            if ch.get('status_atendimento') == 'em_andamento':
                                st.markdown(f"### {formatar_tempo(tempo)}")
                            else:
                                st.write(formatar_tempo(tempo))
                        
                        st.divider()
                else:
                    st.info("📭 Nenhum chamado em atendimento")
                    
            except Exception as e:
                st.error(f"Erro ao carregar chamados em atendimento: {e}")
                import traceback
                st.code(traceback.format_exc())
