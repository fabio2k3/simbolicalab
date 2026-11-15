import sys
from .servidor import servir
servir(int(sys.argv[1]) if len(sys.argv) > 1 else 8000)
