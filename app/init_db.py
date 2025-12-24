# app/init_db.py
from database import criar_tabelas
import os

if __name__ == "__main__":
    print("Inicializando banco de dados e pastas...")
    criar_tabelas()
    print("✅ Banco de dados e pastas prontos.")
