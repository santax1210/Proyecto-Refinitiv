# Guía rápida de Deploy en AWS

## 1. Subir el código al servidor
- En tu PC:
  git add .
  git commit -m "Cambios para deploy"
  git push
- En AWS:
  cd ~/Proyecto-Refinitiv
  git pull

- Backend (Python):
  # Activa el entorno virtual antes de instalar dependencias
  source venv/bin/activate
  pip install -r requirements.txt  # Ejecutar desde la raíz del proyecto
- Frontend (React/Vite):
  cd dashboard-financiero
  npm install

## 3. Build del frontend
- En la carpeta del frontend:
  npm run build
- Esto genera la carpeta dist con los archivos estáticos.

## 4. Configurar Gunicorn y systemd (solo la primera vez o si cambias la config)
- Edita /etc/systemd/system/backend.service para usar 1 worker:
  ExecStart=/home/ubuntu/Proyecto-Refinitiv/venv/bin/gunicorn -w 1 -b 0.0.0.0:5000 api.app:app
- Recarga y reinicia el servicio:
  sudo systemctl daemon-reload
  sudo systemctl restart backend.service
  sudo systemctl status backend.service

## 5. Configurar Nginx (solo la primera vez o si cambias rutas/dominio)
- Edita el archivo de configuración para tu dominio.
- Reinicia Nginx:
  sudo systemctl restart nginx

## 6. Variables de entorno
- Revisa .env.production en el frontend para que apunte al backend correcto.

## 7. Prueba la aplicación
- Accede a tu dominio y verifica que el frontend y backend funcionen.

---

**Notas:**
- Si solo actualizas código, basta con git pull, npm run build, y reiniciar servicios.
- No necesitas reconfigurar Gunicorn/Nginx en cada deploy, solo reiniciarlos si el código o la configuración cambió.
