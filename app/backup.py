#!/usr/bin/env python3
"""
Sistema de Backup - Helpdesk MP Solutions
Cria backups completos do sistema com versionamento
"""

import os
import shutil
import sqlite3
from datetime import datetime
import zipfile
import json

# Configurações
PASTA_BACKUPS = "backups"
MANTER_ULTIMOS = 10  # Quantidade de backups a manter

def criar_pasta_backup():
    """Cria a pasta de backups se não existir."""
    if not os.path.exists(PASTA_BACKUPS):
        os.makedirs(PASTA_BACKUPS)
        print(f"✅ Pasta '{PASTA_BACKUPS}/' criada")

def gerar_nome_backup():
    """Gera nome único para o backup."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return f"backup_{timestamp}"

def backup_banco_dados(pasta_destino):
    """Faz backup do banco de dados."""
    try:
        origem = "data/database.db"
        
        if not os.path.exists(origem):
            print("⚠️ Banco de dados não encontrado")
            return False
        
        destino = os.path.join(pasta_destino, "database.db")
        shutil.copy2(origem, destino)
        
        # Pegar tamanho
        tamanho = os.path.getsize(origem)
        tamanho_mb = tamanho / (1024 * 1024)
        
        print(f"✅ Banco de dados copiado ({tamanho_mb:.2f} MB)")
        return True
    except Exception as e:
        print(f"❌ Erro ao copiar banco: {e}")
        return False

def backup_arquivos(pasta_destino):
    """Faz backup dos arquivos de código."""
    try:
        # Copiar pasta app/
        if os.path.exists("app"):
            destino_app = os.path.join(pasta_destino, "app")
            shutil.copytree("app", destino_app, ignore=shutil.ignore_patterns('__pycache__', '*.pyc'))
            print("✅ Código da aplicação copiado")
        
        # Copiar requirements.txt
        if os.path.exists("requirements.txt"):
            shutil.copy2("requirements.txt", pasta_destino)
            print("✅ requirements.txt copiado")
        
        # Copiar README se existir
        if os.path.exists("README.md"):
            shutil.copy2("README.md", pasta_destino)
        
        return True
    except Exception as e:
        print(f"❌ Erro ao copiar arquivos: {e}")
        return False

def backup_uploads(pasta_destino):
    """Faz backup dos arquivos enviados pelos usuários."""
    try:
        if os.path.exists("uploads") and os.listdir("uploads"):
            destino_uploads = os.path.join(pasta_destino, "uploads")
            shutil.copytree("uploads", destino_uploads)
            
            # Contar arquivos
            total_arquivos = sum([len(files) for r, d, files in os.walk("uploads")])
            print(f"✅ Uploads copiados ({total_arquivos} arquivo(s))")
        else:
            print("ℹ️ Nenhum upload para copiar")
        
        return True
    except Exception as e:
        print(f"❌ Erro ao copiar uploads: {e}")
        return False

def obter_info_banco(caminho_db):
    """Obtém informações sobre o banco de dados."""
    try:
        conn = sqlite3.connect(caminho_db)
        cursor = conn.cursor()
        
        # Contar usuários
        cursor.execute("SELECT COUNT(*) FROM usuarios")
        total_usuarios = cursor.fetchone()[0]
        
        # Contar chamados
        cursor.execute("SELECT COUNT(*) FROM chamados")
        total_chamados = cursor.fetchone()[0]
        
        # Contar anexos
        cursor.execute("SELECT COUNT(*) FROM anexos")
        total_anexos = cursor.fetchone()[0]
        
        conn.close()
        
        return {
            "usuarios": total_usuarios,
            "chamados": total_chamados,
            "anexos": total_anexos
        }
    except:
        return None

def criar_info_backup(pasta_destino, info_banco):
    """Cria arquivo com informações do backup."""
    info = {
        "data_backup": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "versao_sistema": "2.0",
        "banco_dados": info_banco
    }
    
    caminho_info = os.path.join(pasta_destino, "backup_info.json")
    
    with open(caminho_info, 'w', encoding='utf-8') as f:
        json.dump(info, f, indent=4, ensure_ascii=False)
    
    print("✅ Arquivo de informações criado")

def compactar_backup(pasta_backup, nome_backup):
    """Compacta o backup em um arquivo ZIP."""
    try:
        nome_zip = f"{nome_backup}.zip"
        caminho_zip = os.path.join(PASTA_BACKUPS, nome_zip)
        
        with zipfile.ZipFile(caminho_zip, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for root, dirs, files in os.walk(pasta_backup):
                for file in files:
                    caminho_completo = os.path.join(root, file)
                    caminho_relativo = os.path.relpath(caminho_completo, pasta_backup)
                    zipf.write(caminho_completo, caminho_relativo)
        
        # Remover pasta temporária
        shutil.rmtree(pasta_backup)
        
        tamanho = os.path.getsize(caminho_zip)
        tamanho_mb = tamanho / (1024 * 1024)
        
        print(f"✅ Backup compactado: {nome_zip} ({tamanho_mb:.2f} MB)")
        return caminho_zip
    except Exception as e:
        print(f"❌ Erro ao compactar: {e}")
        return None

def limpar_backups_antigos():
    """Remove backups antigos mantendo apenas os mais recentes."""
    try:
        backups = [f for f in os.listdir(PASTA_BACKUPS) if f.startswith("backup_") and f.endswith(".zip")]
        backups.sort(reverse=True)
        
        if len(backups) > MANTER_ULTIMOS:
            for backup in backups[MANTER_ULTIMOS:]:
                caminho = os.path.join(PASTA_BACKUPS, backup)
                os.remove(caminho)
                print(f"🗑️ Backup antigo removido: {backup}")
    except Exception as e:
        print(f"⚠️ Erro ao limpar backups antigos: {e}")

def listar_backups():
    """Lista todos os backups disponíveis."""
    try:
        if not os.path.exists(PASTA_BACKUPS):
            print("📭 Nenhum backup encontrado")
            return
        
        backups = [f for f in os.listdir(PASTA_BACKUPS) if f.endswith(".zip")]
        
        if not backups:
            print("📭 Nenhum backup encontrado")
            return
        
        backups.sort(reverse=True)
        
        print(f"\n📦 Backups Disponíveis ({len(backups)}):")
        print("=" * 80)
        
        for i, backup in enumerate(backups, 1):
            caminho = os.path.join(PASTA_BACKUPS, backup)
            tamanho = os.path.getsize(caminho)
            tamanho_mb = tamanho / (1024 * 1024)
            
            # Extrair data do nome
            try:
                data_str = backup.replace("backup_", "").replace(".zip", "")
                data = datetime.strptime(data_str, "%Y%m%d_%H%M%S")
                data_formatada = data.strftime("%d/%m/%Y %H:%M:%S")
            except:
                data_formatada = "Data desconhecida"
            
            print(f"{i}. {backup}")
            print(f"   📅 Data: {data_formatada}")
            print(f"   💾 Tamanho: {tamanho_mb:.2f} MB")
            print()
    except Exception as e:
        print(f"❌ Erro ao listar backups: {e}")

def executar_backup_completo():
    """Executa o backup completo do sistema."""
    print("\n" + "=" * 80)
    print("💾 INICIANDO BACKUP DO SISTEMA HELPDESK")
    print("=" * 80)
    print()
    
    # Criar pasta de backups
    criar_pasta_backup()
    
    # Gerar nome do backup
    nome_backup = gerar_nome_backup()
    pasta_temp = os.path.join(PASTA_BACKUPS, nome_backup)
    os.makedirs(pasta_temp)
    
    print(f"📦 Nome do backup: {nome_backup}")
    print()
    
    # Obter informações do banco
    info_banco = None
    if os.path.exists("data/database.db"):
        info_banco = obter_info_banco("data/database.db")
        if info_banco:
            print(f"📊 Estatísticas do banco:")
            print(f"   👥 Usuários: {info_banco['usuarios']}")
            print(f"   🎫 Chamados: {info_banco['chamados']}")
            print(f"   📎 Anexos: {info_banco['anexos']}")
            print()
    
    # Executar backups
    print("🔄 Copiando arquivos...")
    print()
    
    sucesso = True
    sucesso &= backup_banco_dados(pasta_temp)
    sucesso &= backup_arquivos(pasta_temp)
    sucesso &= backup_uploads(pasta_temp)
    
    if info_banco:
        criar_info_backup(pasta_temp, info_banco)
    
    print()
    
    if sucesso:
        # Compactar
        print("📦 Compactando backup...")
        caminho_zip = compactar_backup(pasta_temp, nome_backup)
        
        if caminho_zip:
            print()
            print("=" * 80)
            print("✅ BACKUP CONCLUÍDO COM SUCESSO!")
            print("=" * 80)
            print(f"\n📁 Local: {caminho_zip}")
            print()
            
            # Limpar backups antigos
            limpar_backups_antigos()
            
            return True
    else:
        print("\n❌ Backup falhou!")
        # Limpar pasta temporária se existir
        if os.path.exists(pasta_temp):
            shutil.rmtree(pasta_temp)
        return False

def menu_principal():
    """Menu principal do sistema de backup."""
    print("\n" + "=" * 80)
    print("💾 SISTEMA DE BACKUP - HELPDESK MP SOLUTIONS")
    print("=" * 80)
    print("\nOpções:")
    print("1. Criar novo backup")
    print("2. Listar backups existentes")
    print("3. Sair")
    print()
    
    escolha = input("Escolha uma opção (1-3): ").strip()
    
    if escolha == "1":
        executar_backup_completo()
    elif escolha == "2":
        listar_backups()
    elif escolha == "3":
        print("\n👋 Até logo!")
        return False
    else:
        print("\n❌ Opção inválida!")
    
    return True

if __name__ == "__main__":
    while True:
        if not menu_principal():
            break
        
        input("\nPressione ENTER para continuar...")
        print("\n" * 2)
