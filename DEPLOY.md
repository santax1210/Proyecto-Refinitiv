# Deploy esencial en AWS

1. **Sube tus cambios a GitHub:**
  ```bash
  git add .
  git commit -m "Cambios"
  git push
  ```

2. **Actualiza el código en AWS:**
  ```bash
  cd ~/Proyecto-Refinitiv
  git pull
  ```

3. **Activa el entorno virtual e instala dependencias:**
  ```bash
  source venv/bin/activate
  pip install -r requirements.txt
  ```

4. **Edita el archivo .env si es necesario:**
  ```bash
  nano .env
  # (JWT_SECRET_KEY, APP_USERNAME, APP_PASSWORD, etc)
  ```

5. **Instala y build del frontend:**
  ```bash
  cd dashboard-financiero
  npm install
  npm run build
  ```

6. **Reinicia el backend:**
  ```bash
  sudo systemctl restart backend
  sudo systemctl status backend
  ```

7. **(Solo si cambiaste Nginx) Reinicia Nginx:**
  ```bash
  sudo systemctl restart nginx
  ```

¡Listo! Accede a tu dominio y prueba la app.
