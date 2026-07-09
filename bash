# 1. Sacamos los archivos principales de la carpeta src hacia la raíz real
git mv src/app.py ./
git mv src/requirements.txt ./
git mv src/README.md ./
git mv src/bash ./ 2>/dev/null || true
git mv src/estructura ./ 2>/dev/null || true

# 2. Confirmamos el movimiento creando el bloque de cambios (commit)
git commit -m "Fix: Movido app.py, requirements y utilidades a la raíz del repositorio"

# 3. Empujamos los cambios directo a GitHub
git push origin main
