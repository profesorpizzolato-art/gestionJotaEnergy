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
