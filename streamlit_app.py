"""
Entry point para Streamlit Cloud
Este arquivo deve estar na RAIZ do projeto
"""

import sys
import os

# Adicionar pasta app ao Python path
app_dir = os.path.join(os.path.dirname(__file__), 'app')
if app_dir not in sys.path:
    sys.path.insert(0, app_dir)

# Importar e executar main do app
if __name__ == "__main__":
    from app.main import main
    main()
