# 1. Verificá los archivos creados/modificados
git status

# 2. Agregá los archivos al área de preparación
git add src/modules/pumping/calculator.py app.py

# 3. Guardá los cambios con un mensaje claro
git commit -m "Feat: Implementado módulo de cálculo de cementación con colores corporativos"

# 4. Subilos a tu repositorio remoto en GitHub
git push origin main
git add src/modules/pumping/calculator.py app.py
git commit -m "Feat: Expandido calculador con agua de mezcla y aditivos GPS"
git push origin main
git add src/modules/pumping/services.py app.py
git commit -m "Feat: Conectada la UI de cálculos de bombeo con la base de datos relacional"
git push origin main
git add app.py
git commit -m "Fix: Solucionado path de modulos y agregada interfaz multi-servicio"
git push origin main
# 1. Agrega el app.py corregido y los inicializadores si no estaban
git add app.py
git add src/__init__.py src/database/__init__.py src/modules/__init__.py 2>/dev/null || git add app.py

# 2. Crea el commit del fix definitivo
git commit -m "Fix: Eliminado prefijo src de imports para corregir crash en linea 11"

# 3. Súbelo a GitHub
git push origin main
git add app.py
git commit -m "Fix: Implementadas rutas absolutas con src. combinadas con sys.path para Streamlit Cloud"
git push origin main
