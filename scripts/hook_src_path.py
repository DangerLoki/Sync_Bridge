# Runtime hook executado pelo PyInstaller antes de qualquer import do script principal.
# Insere o diretório raiz do bundle (sys._MEIPASS) no sys.path para que os
# imports absolutos como "from src.application..." funcionem corretamente.
import sys

if hasattr(sys, "_MEIPASS"):
    sys.path.insert(0, sys._MEIPASS)
