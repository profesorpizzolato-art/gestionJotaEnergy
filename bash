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
git add app.py src/modules/operations/models.py
git commit -m "Módulo Operativo e Higiene: Añadido Checklist HSE y campos de volumen real vs diseño"
git push origin main
git add app.py
git commit -m "Fix: Reparado y expandido app.py con integracion HSE y volumenes reales"
git push origin main
git add src/database/connection.py
git commit -m "Fix: Corregido import incorrecto de create_index en connection.py"
git push origin main
git add src/modules/pumping/services.py
git commit -m "Fix: Corregida ruta de importación de Intervencion en services.py añadiendo prefijo src"
git push origin main
git add requirements.txt src/modules/pumping/services.py app.py
git commit -m "Feature: Agregados reportes PDF, simulador logistico e ingenieria en pestañas de Fractura y P&A"
git push origin main
git add app.py
git commit -m "Feature: Acoplada vista e interacciones del Almacen Mendoza real en el frontend"
git push origin main
# Crear estructura de carpetas
mkdir -p src/database src/modules/operations src/modules/pumping

# Agregar los archivos a Git, confirmar y subir
git add src/ app.py
git commit -m "Refactor: Modularización estructural completa del ERP Jota Energy"
git push origin main
