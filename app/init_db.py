# app/init_db.py
"""
Script de inicialização do banco de dados
Execute uma vez para criar todas as tabelas
"""

import os
import sys

# Adicionar path
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

from database import criar_tabelas

if __name__ == "__main__":
    print("="*50)
    print("INICIALIZAÇÃO DO BANCO DE DADOS")
    print("="*50)
    
    print("\n📦 Criando pastas necessárias...")
    
    for pasta in ['data', 'uploads', 'backups']:
        if not os.path.exists(pasta):
            os.makedirs(pasta)
            print(f"   ✅ Pasta '{pasta}' criada")
        else:
            print(f"   ✓ Pasta '{pasta}' já existe")
    
    print("\n🗄️ Criando tabelas do banco de dados...")
    resultado = criar_tabelas()
    
    if resultado:
        print("\n✅ Banco de dados inicializado com sucesso!")
        print("\n📋 Usuário padrão criado:")
        print("   Usuário: admin")
        print("   Senha: admin123")
        print("\n⚠️ IMPORTANTE: Altere a senha do admin após o primeiro login!")
    else:
        print("\n❌ Erro ao inicializar banco de dados")
    
    print("\n" + "="*50)
