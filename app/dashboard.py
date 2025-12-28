# app/dashboard.py
"""
Dashboard do Sistema Helpdesk
"""

import streamlit as st
import pandas as pd
from database import conectar, buscar_estatisticas_usuario
from utils import formatar_tempo, badge_status, badge_prioridade

def formatar_data_br(data):
    """Formata data para padrão brasileiro."""
    if not data:
        return "N/A"
    try:
        from datetime import datetime
        if isinstance(data, str):
            data = datetime.strptime(data.split('.')[0], "%Y-%m-%d %H:%M:%S")
        return data.strftime('%d/%m/%Y %H:%M')
    except:
        return str(data)

def buscar_emails_enviados(limite=100):
    """Busca histórico de e-mails enviados."""
    try:
        conn = conectar()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT 
                e.id,
                e.data_envio,
                e.destinatario,
                e.assunto,
                e.tipo,
                e.chamado_id,
                e.sucesso,
                e.erro,
                c.usuario as usuario_chamado
            FROM emails_enviados e
            LEFT JOIN chamados c ON e.chamado_id = c.id
            ORDER BY e.data_envio DESC
            LIMIT ?
        """, (limite,))
        emails = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return emails
    except Exception as e:
        print(f"Erro ao buscar emails: {e}")
        return []

def tela_dashboard():
    """Tela de Dashboard com estatísticas."""
    st.subheader("📊 Dashboard")
    
    usuario = st.session_state.get('usuario')
    perfil = st.session_state.get('perfil')
    
    if not usuario:
        st.error("Usuário não autenticado")
        return
    
    # Verificar se é admin/suporte
    eh_admin = perfil in ['admin', 'suporte', 'Admin', 'Suporte', 'ADMIN', 'SUPORTE']
    
    # ========== VISÃO GERAL (Cards no topo) ==========
    estatisticas = buscar_estatisticas_usuario(usuario, perfil if eh_admin else 'cliente')
    
    if not eh_admin:
        st.info("📊 Seus Chamados")
    
    col1, col2, col3, col4, col5 = st.columns(5)
    
    col1.metric("📋 Total", estatisticas["total"])
    col2.metric("🆕 Novos", estatisticas["novos"])
    col3.metric("🔄 Em Atendimento", estatisticas["em_atendimento"])
    
    # Contar aguardando finalização e finalizados
    try:
        conn = conectar()
        cursor = conn.cursor()
        if eh_admin:
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
        
        col4.metric("⏳ Aguardando", aguardando)
        col5.metric("✅ Finalizados", finalizados)
    except Exception as e:
        col4.metric("⏳ Aguardando", 0)
        col5.metric("✅ Finalizados", 0)
        print(f"Erro ao buscar contadores: {e}")
    
    st.markdown("---")
    
    # ========== DASHBOARD ESPECÍFICO POR PERFIL ==========
    
    if eh_admin:
        # ========== DASHBOARD ADMIN ==========
        st.subheader("📊 Visão Administrativa")
        
        # Abas principais
        tab_empresa, tab_usuario, tab_tempo, tab_emails, tab_logs = st.tabs([
            "🏢 Por Empresa", 
            "👤 Por Usuário", 
            "⏱️ Tempo de Atendimento",
            "📧 E-mails Enviados",
            "📋 Logs do Sistema"
        ])
        
        # ========== TAB: POR EMPRESA ==========
        with tab_empresa:
            try:
                conn = conectar()
                cursor = conn.cursor()
                
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
                    df_empresas = pd.DataFrame([
                        {
                            'Empresa': emp['empresa'],
                            'Total': emp['total'],
                            'Novos': emp['novos'],
                            'Em Atend.': emp['em_atendimento'],
                            'Aguardando': emp['aguardando'],
                            'Finalizados': emp['finalizados'],
                            'Tempo Médio': formatar_tempo(int(emp['tempo_medio'])) if emp['tempo_medio'] else 'N/A'
                        }
                        for emp in empresas
                    ])
                    
                    st.dataframe(df_empresas, use_container_width=True, hide_index=True)
                    
                    # Gráfico
                    st.bar_chart(df_empresas.set_index('Empresa')['Total'])
                else:
                    st.info("📭 Nenhuma empresa com chamados")
                    
            except Exception as e:
                st.error(f"Erro ao carregar dados: {e}")
        
        # ========== TAB: POR USUÁRIO ==========
        with tab_usuario:
            try:
                conn = conectar()
                cursor = conn.cursor()
                
                cursor.execute("""
                    SELECT 
                        c.usuario,
                        u.nome_completo,
                        u.empresa,
                        COUNT(c.id) as total,
                        COUNT(CASE WHEN c.status = 'Novo' THEN 1 END) as novos,
                        COUNT(CASE WHEN c.status = 'Em atendimento' THEN 1 END) as em_atendimento,
                        COUNT(CASE WHEN c.status = 'Finalizado' THEN 1 END) as finalizados
                    FROM chamados c
                    LEFT JOIN usuarios u ON c.usuario = u.usuario
                    GROUP BY c.usuario
                    ORDER BY total DESC
                """)
                
                usuarios_stats = [dict(row) for row in cursor.fetchall()]
                conn.close()
                
                if usuarios_stats:
                    df_usuarios = pd.DataFrame([
                        {
                            'Usuário': u['usuario'],
                            'Nome': u.get('nome_completo') or 'N/A',
                            'Empresa': u.get('empresa') or 'N/A',
                            'Total': u['total'],
                            'Novos': u['novos'],
                            'Em Atend.': u['em_atendimento'],
                            'Finalizados': u['finalizados']
                        }
                        for u in usuarios_stats
                    ])
                    
                    st.dataframe(df_usuarios, use_container_width=True, hide_index=True)
                else:
                    st.info("📭 Nenhum usuário com chamados")
                    
            except Exception as e:
                st.error(f"Erro ao carregar dados: {e}")
        
        # ========== TAB: TEMPO DE ATENDIMENTO ==========
        with tab_tempo:
            try:
                conn = conectar()
                cursor = conn.cursor()
                
                cursor.execute("""
                    SELECT 
                        id, assunto, usuario, atendente, status,
                        tempo_atendimento_segundos, retornos,
                        data_abertura, data_fim_atendimento
                    FROM chamados
                    WHERE tempo_atendimento_segundos > 0
                    ORDER BY tempo_atendimento_segundos DESC
                    LIMIT 20
                """)
                
                chamados_tempo = [dict(row) for row in cursor.fetchall()]
                conn.close()
                
                if chamados_tempo:
                    df_tempo = pd.DataFrame([
                        {
                            'ID': ch['id'],
                            'Assunto': ch['assunto'][:30] + '...' if len(ch['assunto']) > 30 else ch['assunto'],
                            'Usuário': ch['usuario'],
                            'Atendente': ch.get('atendente') or 'N/A',
                            'Status': ch['status'],
                            'Tempo': formatar_tempo(ch['tempo_atendimento_segundos']),
                            'Retornos': ch.get('retornos', 0)
                        }
                        for ch in chamados_tempo
                    ])
                    
                    st.dataframe(df_tempo, use_container_width=True, hide_index=True)
                    
                    # Estatísticas de tempo
                    tempos = [ch['tempo_atendimento_segundos'] for ch in chamados_tempo if ch['tempo_atendimento_segundos']]
                    if tempos:
                        col1, col2, col3 = st.columns(3)
                        col1.metric("⏱️ Tempo Médio", formatar_tempo(int(sum(tempos) / len(tempos))))
                        col2.metric("⚡ Tempo Mínimo", formatar_tempo(min(tempos)))
                        col3.metric("🐢 Tempo Máximo", formatar_tempo(max(tempos)))
                else:
                    st.info("📭 Nenhum chamado com tempo registrado")
                    
            except Exception as e:
                st.error(f"Erro ao carregar dados: {e}")
        
        # ========== TAB: E-MAILS ENVIADOS ==========
        with tab_emails:
            st.write("### 📧 Histórico de E-mails Enviados")
            
            col1, col2 = st.columns([2, 1])
            with col1:
                filtro_tipo = st.selectbox(
                    "Filtrar por tipo",
                    ["Todos", "novo_chamado_admin", "novo_chamado_cliente", "chamado_concluido", 
                     "chamado_retornado_admin", "chamado_retornado_cliente", "chamado_finalizado"],
                    key="filtro_tipo_email"
                )
            with col2:
                limite_emails = st.selectbox("Quantidade", [50, 100, 200, 500], key="limite_emails")
            
            emails = buscar_emails_enviados(limite_emails)
            
            if filtro_tipo != "Todos":
                emails = [e for e in emails if e.get('tipo') == filtro_tipo]
            
            if emails:
                # Criar DataFrame com as colunas solicitadas
                df_emails = pd.DataFrame([
                    {
                        'Data': formatar_data_br(e['data_envio']),
                        'Hora': e['data_envio'].split(' ')[1][:8] if ' ' in str(e['data_envio']) else 'N/A',
                        'Usuário': e.get('usuario_chamado') or e['destinatario'].split('@')[0],
                        'Destinatário': e['destinatario'],
                        'Assunto': e['assunto'][:40] + '...' if len(e['assunto']) > 40 else e['assunto'],
                        'Chamado': f"#{e['chamado_id']}" if e['chamado_id'] else 'N/A',
                        'Tipo': e.get('tipo', 'N/A'),
                        'Status': '✅ Enviado' if e['sucesso'] else f"❌ Erro: {e.get('erro', 'Desconhecido')[:20]}"
                    }
                    for e in emails
                ])
                
                st.dataframe(df_emails, use_container_width=True, hide_index=True)
                
                # Estatísticas
                total_emails = len(emails)
                enviados_ok = len([e for e in emails if e['sucesso']])
                enviados_erro = total_emails - enviados_ok
                
                col1, col2, col3 = st.columns(3)
                col1.metric("📧 Total", total_emails)
                col2.metric("✅ Enviados", enviados_ok)
                col3.metric("❌ Erros", enviados_erro)
                
            else:
                st.info("📭 Nenhum e-mail encontrado")
                st.caption("Os e-mails aparecerão aqui quando forem enviados pelo sistema.")
        
        # ========== TAB: LOGS ==========
        with tab_logs:
            try:
                from database import buscar_logs_sistema
                
                col1, col2 = st.columns([2, 1])
                with col1:
                    filtro_acao = st.text_input("Filtrar por ação", key="filtro_acao_logs")
                with col2:
                    limite = st.selectbox("Quantidade", [50, 100, 200, 500], key="limite_logs")
                
                logs = buscar_logs_sistema(limite=limite)
                
                if filtro_acao:
                    logs = [l for l in logs if filtro_acao.lower() in l['acao'].lower()]
                
                if logs:
                    df_logs = pd.DataFrame([
                        {
                            'Data/Hora': l['data_hora'],
                            'Ação': l['acao'],
                            'Usuário': l.get('usuario') or 'N/A',
                            'Detalhes': (l.get('detalhes', '')[:50] + '...') if l.get('detalhes') and len(l.get('detalhes', '')) > 50 else (l.get('detalhes') or '')
                        }
                        for l in logs
                    ])
                    
                    st.dataframe(df_logs, use_container_width=True, hide_index=True)
                else:
                    st.info("📭 Nenhum log encontrado")
                    
            except Exception as e:
                st.error(f"Erro ao carregar logs: {e}")
    
    else:
        # ========== DASHBOARD CLIENTE ==========
        if estatisticas["total"] > 0:
            st.subheader("📈 Distribuição dos seus chamados")
            
            chart_data = pd.DataFrame({
                'Status': ['Novos', 'Em Atendimento', 'Aguardando', 'Finalizados'],
                'Quantidade': [
                    estatisticas["novos"], 
                    estatisticas["em_atendimento"], 
                    aguardando,
                    finalizados
                ]
            })
            
            st.bar_chart(chart_data.set_index('Status'))
            
            # Últimos chamados
            st.subheader("📋 Seus Últimos Chamados")
            
            try:
                conn = conectar()
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT id, assunto, status, prioridade, data_abertura
                    FROM chamados
                    WHERE usuario = ?
                    ORDER BY id DESC
                    LIMIT 5
                """, (usuario,))
                
                ultimos = [dict(row) for row in cursor.fetchall()]
                conn.close()
                
                if ultimos:
                    for ch in ultimos:
                        st.markdown(f"""
                        {badge_status(ch['status'])} {badge_prioridade(ch['prioridade'])} 
                        **#{ch['id']}** - {ch['assunto'][:40]}...
                        """)
            except:
                pass
        else:
            st.info("📭 Você ainda não possui chamados. Abra seu primeiro chamado na aba 'Chamados'!")
