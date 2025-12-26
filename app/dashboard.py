# app/dashboard.py - VERSÃO CORRIGIDA
import streamlit as st
import pandas as pd
from database import (
    buscar_estatisticas_usuario, 
    conectar, 
    obter_tempo_atendimento,
    buscar_estatisticas_por_empresa,
    buscar_chamados_com_tempo
)
from utils import formatar_tempo, badge_status, badge_prioridade

def formatar_data_br(data):
    """Formata data para padrão brasileiro."""
    if data is None:
        return "N/A"
    if isinstance(data, str):
        try:
            from datetime import datetime
            data = datetime.strptime(data.split('.')[0], "%Y-%m-%d %H:%M:%S")
            return data.strftime('%d/%m/%Y %H:%M')
        except:
            return data
    return str(data)


def tela_dashboard():
    st.subheader("📊 Dashboard")
    
    usuario = st.session_state.get('usuario')
    perfil = st.session_state.get('perfil')
    
    if not usuario:
        st.error("Usuário não autenticado")
        return
    
    # ========== VISÃO GERAL (Cards no topo) ==========
    estatisticas = buscar_estatisticas_usuario(usuario, perfil)
    
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
    
    st.markdown("---")
    
    # ========== DASHBOARD ESPECÍFICO POR PERFIL ==========
    
    if perfil == "admin":
        # ========== DASHBOARD ADMIN: POR CLIENTE/EMPRESA ==========
        st.subheader("📊 Chamados por Cliente/Empresa")
        
        # Abas principais
        tab_empresa, tab_usuario, tab_tempo, tab_andamento = st.tabs([
            "🏢 Por Empresa", 
            "👤 Por Usuário", 
            "⏱️ Tempo de Atendimento",
            "▶️ Em Andamento"
        ])
        
        # ========== TAB: POR EMPRESA ==========
        with tab_empresa:
            try:
                conn = conectar()
                cursor = conn.cursor()
                
                # Buscar dados agrupados por empresa
                cursor.execute("""
                    SELECT 
                        COALESCE(u.empresa, 'Sem empresa') as empresa,
                        COUNT(DISTINCT c.id) as total,
                        COUNT(DISTINCT CASE WHEN c.status = 'Novo' THEN c.id END) as novos,
                        COUNT(DISTINCT CASE WHEN c.status = 'Em atendimento' THEN c.id END) as em_atendimento,
                        COUNT(DISTINCT CASE WHEN c.status = 'Aguardando Finalização' THEN c.id END) as aguardando,
                        COUNT(DISTINCT CASE WHEN c.status = 'Finalizado' THEN c.id END) as finalizados,
                        AVG(CASE WHEN c.tempo_atendimento_segundos > 0 THEN c.tempo_atendimento_segundos END) as tempo_medio
                    FROM usuarios u
                    LEFT JOIN chamados c ON u.usuario = c.usuario
                    GROUP BY u.empresa
                    HAVING total > 0
                    ORDER BY total DESC
                """)
                
                empresas = [dict(row) for row in cursor.fetchall()]
                conn.close()
                
                if empresas:
                    # Criar DataFrame para visualização
                    df_empresas = pd.DataFrame([
                        {
                            'Empresa': emp['empresa'],
                            'Total': emp['total'],
                            'Novos': emp['novos'],
                            'Em Atendimento': emp['em_atendimento'],
                            'Aguardando': emp['aguardando'],
                            'Finalizados': emp['finalizados'],
                            'Tempo Médio': formatar_tempo(int(emp['tempo_medio'])) if emp['tempo_medio'] else 'N/A'
                        }
                        for emp in empresas
                    ])
                    
                    st.dataframe(df_empresas, use_container_width=True, hide_index=True)
                    
                    # Detalhes por empresa (expansível)
                    st.divider()
                    st.write("**📋 Detalhes por Empresa**")
                    
                    for emp in empresas:
                        with st.expander(f"🏢 {emp['empresa']} - {emp['total']} chamados"):
                            col_e1, col_e2, col_e3, col_e4, col_e5 = st.columns(5)
                            
                            col_e1.metric("Total", emp['total'])
                            col_e2.metric("Novos", emp['novos'])
                            col_e3.metric("Em Atend.", emp['em_atendimento'])
                            col_e4.metric("Aguardando", emp['aguardando'])
                            col_e5.metric("Finalizados", emp['finalizados'])
                            
                            if emp.get('tempo_medio'):
                                st.write(f"**⏱️ Tempo Médio:** {formatar_tempo(int(emp['tempo_medio']))}")
                            
                            # Buscar chamados desta empresa
                            conn = conectar()
                            cursor = conn.cursor()
                            cursor.execute("""
                                SELECT c.id, c.assunto, c.status, c.prioridade, c.usuario, c.data_abertura
                                FROM chamados c
                                JOIN usuarios u ON c.usuario = u.usuario
                                WHERE u.empresa = ?
                                ORDER BY c.id DESC
                                LIMIT 10
                            """, (emp['empresa'] if emp['empresa'] != 'Sem empresa' else None,))
                            
                            chamados_emp = [dict(row) for row in cursor.fetchall()]
                            conn.close()
                            
                            if chamados_emp:
                                st.write("**📋 Últimos Chamados:**")
                                for ch in chamados_emp:
                                    status_badge = badge_status(ch['status'])
                                    prior_badge = badge_prioridade(ch['prioridade'])
                                    st.write(f"{status_badge} {prior_badge} **#{ch['id']}** - {ch['assunto']} ({ch['usuario']})")
                
                else:
                    st.info("📭 Nenhuma empresa com chamados")
                    
            except Exception as e:
                st.error(f"Erro ao carregar dados por empresa: {e}")
        
        # ========== TAB: POR USUÁRIO ==========
        with tab_usuario:
            try:
                conn = conectar()
                cursor = conn.cursor()
                
                # Buscar dados agrupados por usuário
                cursor.execute("""
                    SELECT 
                        c.usuario,
                        u.nome_completo,
                        u.empresa,
                        COUNT(c.id) as total,
                        COUNT(CASE WHEN c.status = 'Novo' THEN 1 END) as novos,
                        COUNT(CASE WHEN c.status = 'Em atendimento' THEN 1 END) as em_atendimento,
                        COUNT(CASE WHEN c.status = 'Aguardando Finalização' THEN 1 END) as aguardando,
                        COUNT(CASE WHEN c.status = 'Finalizado' THEN 1 END) as finalizados
                    FROM chamados c
                    LEFT JOIN usuarios u ON c.usuario = u.usuario
                    GROUP BY c.usuario
                    ORDER BY total DESC
                """)
                
                usuarios_stats = [dict(row) for row in cursor.fetchall()]
                conn.close()
                
                if usuarios_stats:
                    # Filtros
                    col_f1, col_f2 = st.columns(2)
                    
                    with col_f1:
                        filtro_empresa_user = st.selectbox(
                            "Filtrar por empresa",
                            ["Todas"] + sorted(list(set([u['empresa'] or 'Sem empresa' for u in usuarios_stats]))),
                            key="filtro_empresa_usuario"
                        )
                    
                    with col_f2:
                        busca_usuario = st.text_input("Buscar usuário", placeholder="Digite o nome...", key="busca_usuario")
                    
                    # Aplicar filtros
                    usuarios_filtrados = usuarios_stats
                    
                    if filtro_empresa_user != "Todas":
                        usuarios_filtrados = [
                            u for u in usuarios_filtrados 
                            if (u['empresa'] or 'Sem empresa') == filtro_empresa_user
                        ]
                    
                    if busca_usuario:
                        usuarios_filtrados = [
                            u for u in usuarios_filtrados 
                            if busca_usuario.lower() in (u['usuario'] or '').lower() 
                            or busca_usuario.lower() in (u['nome_completo'] or '').lower()
                        ]
                    
                    # Criar DataFrame
                    df_usuarios = pd.DataFrame([
                        {
                            'Usuário': u['usuario'],
                            'Nome': u['nome_completo'] or 'N/A',
                            'Empresa': u['empresa'] or 'N/A',
                            'Total': u['total'],
                            'Novos': u['novos'],
                            'Em Atend.': u['em_atendimento'],
                            'Aguardando': u['aguardando'],
                            'Finalizados': u['finalizados']
                        }
                        for u in usuarios_filtrados
                    ])
                    
                    st.dataframe(df_usuarios, use_container_width=True, hide_index=True)
                    
                    # Detalhes expandíveis
                    st.divider()
                    st.write(f"**📋 Detalhes ({len(usuarios_filtrados)} usuários)**")
                    
                    for u in usuarios_filtrados:
                        empresa_txt = f" ({u['empresa']})" if u['empresa'] else ""
                        
                        with st.expander(f"👤 {u['usuario']}{empresa_txt} - {u['total']} chamados"):
                            col_u1, col_u2, col_u3, col_u4, col_u5 = st.columns(5)
                            
                            col_u1.metric("Total", u['total'])
                            col_u2.metric("Novos", u['novos'])
                            col_u3.metric("Em Atend.", u['em_atendimento'])
                            col_u4.metric("Aguardando", u['aguardando'])
                            col_u5.metric("Finalizados", u['finalizados'])
                            
                            # Buscar chamados deste usuário
                            conn = conectar()
                            cursor = conn.cursor()
                            cursor.execute("""
                                SELECT id, assunto, status, prioridade, data_abertura
                                FROM chamados
                                WHERE usuario = ?
                                ORDER BY id DESC
                                LIMIT 10
                            """, (u['usuario'],))
                            
                            chamados_user = [dict(row) for row in cursor.fetchall()]
                            conn.close()
                            
                            if chamados_user:
                                st.write("**📋 Últimos Chamados:**")
                                for ch in chamados_user:
                                    status_badge = badge_status(ch['status'])
                                    prior_badge = badge_prioridade(ch['prioridade'])
                                    st.write(f"{status_badge} {prior_badge} **#{ch['id']}** - {ch['assunto']}")
                
                else:
                    st.info("📭 Nenhum usuário com chamados")
                    
            except Exception as e:
                st.error(f"Erro ao carregar dados por usuário: {e}")
        
        # ========== TAB: TEMPO DE ATENDIMENTO ==========
        with tab_tempo:
            st.subheader("⏱️ Tempo de Atendimento")
            
            try:
                chamados = buscar_chamados_com_tempo()
                
                if chamados:
                    # Filtros
                    col_tf1, col_tf2 = st.columns(2)
                    
                    with col_tf1:
                        filtro_empresa_tempo = st.selectbox(
                            "Filtrar por empresa",
                            ["Todas"] + sorted(list(set([ch.get('empresa') or 'Sem empresa' for ch in chamados]))),
                            key="filtro_empresa_tempo"
                        )
                    
                    with col_tf2:
                        limite_registros = st.selectbox("Mostrar", [10, 25, 50, 100], index=2, key="limite_registros_tempo")
                    
                    # Aplicar filtro
                    chamados_filtrados = chamados
                    
                    if filtro_empresa_tempo != "Todas":
                        chamados_filtrados = [
                            ch for ch in chamados_filtrados 
                            if (ch.get('empresa') or 'Sem empresa') == filtro_empresa_tempo
                        ]
                    
                    chamados_filtrados = chamados_filtrados[:limite_registros]
                    
                    # Criar DataFrame
                    df_tempo = pd.DataFrame([
                        {
                            'ID': f"#{ch['id']}",
                            'Assunto': ch['assunto'][:40] + '...' if len(ch['assunto']) > 40 else ch['assunto'],
                            'Cliente': ch['usuario'],
                            'Empresa': ch.get('empresa') or 'N/A',
                            'Atendente': ch.get('atendente') or 'N/A',
                            'Tempo': formatar_tempo(ch.get('tempo_atendimento_segundos', 0)),
                            'Abertura': formatar_data_br(ch.get('data_abertura'))
                        }
                        for ch in chamados_filtrados
                    ])
                    
                    st.dataframe(df_tempo, use_container_width=True, hide_index=True)
                    
                    # Estatísticas
                    st.divider()
                    col_st1, col_st2, col_st3 = st.columns(3)
                    
                    tempos = [ch.get('tempo_atendimento_segundos', 0) for ch in chamados_filtrados]
                    tempo_medio = sum(tempos) / len(tempos) if tempos else 0
                    tempo_min = min(tempos) if tempos else 0
                    tempo_max = max(tempos) if tempos else 0
                    
                    col_st1.metric("⏱️ Tempo Médio", formatar_tempo(int(tempo_medio)))
                    col_st2.metric("🏃 Mais Rápido", formatar_tempo(tempo_min))
                    col_st3.metric("🐌 Mais Lento", formatar_tempo(tempo_max))
                
                else:
                    st.info("📭 Nenhum chamado concluído ainda")
                    
            except Exception as e:
                st.error(f"Erro ao carregar tempos: {e}")
                import traceback
                st.code(traceback.format_exc())
        
        # ========== TAB: EM ANDAMENTO ==========
        with tab_andamento:
            st.subheader("▶️ Chamados em Andamento")
            
            try:
                conn = conectar()
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT COUNT(*) as total FROM chamados WHERE status = 'Em atendimento'
                """)
                total_atendimento = cursor.fetchone()['total']
                conn.close()
                
                if total_atendimento > 0:
                    if st.button("🔄 Atualizar Tempos", key="btn_atualizar_andamento"):
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
                    
                    chamados_andamento = cursor.fetchall()
                    conn.close()
                    
                    for ch in chamados_andamento:
                        tempo = obter_tempo_atendimento(ch['id'])
                        status_emoji = "⏸️" if ch.get('status_atendimento') == "pausado" else "▶️"
                        
                        col_a, col_b = st.columns([3, 1])
                        
                        with col_a:
                            empresa_txt = f" ({ch.get('empresa', '')})" if ch.get('empresa') else ""
                            st.write(f"{status_emoji} **#{ch['id']}** - {ch['assunto']}")
                            st.caption(f"Cliente: {ch['usuario']}{empresa_txt} | Atendente: {ch.get('atendente', 'N/A')}")
                        
                        with col_b:
                            if ch.get('status_atendimento') == 'em_andamento':
                                st.markdown(f"### {formatar_tempo(tempo)}")
                            else:
                                st.write(formatar_tempo(tempo))
                        
                        st.divider()
                else:
                    st.info("📭 Nenhum chamado em atendimento no momento")
                    
            except Exception as e:
                st.error(f"Erro ao carregar chamados em andamento: {e}")
                import traceback
                st.code(traceback.format_exc())
    
    else:
        # ========== DASHBOARD CLIENTE: SIMPLES ==========
        if estatisticas["total"] > 0:
            st.subheader("📈 Distribuição dos seus chamados")
            
            chart_data = pd.DataFrame({
                'Quantidade': [
                    estatisticas["novos"], 
                    estatisticas["em_atendimento"], 
                    aguardando,
                    finalizados
                ]
            }, index=['Novos', 'Em Atendimento', 'Aguardando', 'Finalizados'])
            
            st.bar_chart(chart_data)
