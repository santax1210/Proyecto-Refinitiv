# Dashboard Financiero (Frontend)

Este frontend está construido con React y Vite.

## Instalación de dependencias

1. Entra a la carpeta del frontend:
   
	cd dashboard-financiero

2. Instala las dependencias:
   
	npm install

## Ejecución en modo desarrollo

npm run dev

Esto levantará el servidor de desarrollo en http://localhost:5173 (o el puerto que indique la consola).

## Generar build de producción

npm run build

El resultado estará en la carpeta dist/.

## Previsualizar build de producción

npm run preview

## Notas
- No es necesario subir la carpeta node_modules ni dist al repositorio (ya están en .gitignore).
- Si necesitas variables de entorno, crea un archivo .env siguiendo el ejemplo de .env.example (si existe).
- Para conectar con el backend, asegúrate de que la URL de la API esté correctamente configurada en los servicios del frontend.
