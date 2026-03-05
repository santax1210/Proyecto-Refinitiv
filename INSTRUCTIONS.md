# 🚀 Sistema de Validación de Allocations

Sistema completo con backend Flask + frontend React para validación automatizada de allocations financieras.

## 📋 Requisitos

- Python 3.11+
- Node.js 18+
- npm o yarn

## 🛠️ Instalación

### 1. Backend (API Flask)

```bash
# Activar entorno virtual
.\venv\Scripts\Activate.ps1

# Instalar dependencias de Flask
pip install -r api/requirements.txt
```

### 2. Frontend (React + Vite)

```bash
# Navegar a la carpeta del frontend
cd dashboard-financiero

# Instalar dependencias
npm install

# Volver a la raíz
cd ..
```

## ▶️ Ejecución

### Opción 1: Iniciar manualmente (2 terminales)

**Terminal 1 - Backend:**
```powershell
# Activar entorno virtual
.\venv\Scripts\Activate.ps1

# Iniciar API Flask
python api/app.py
```
El backend estará en: `http://localhost:5000`

**Terminal 2 - Frontend:**
```powershell
# Navegar al frontend
cd dashboard-financiero

# Iniciar servidor de desarrollo
npm run dev
```
El frontend estará en: `http://localhost:5173`

### Opción 2: Script automatizado

```powershell
# Ejecutar script de inicio
.\start.ps1
```

Este script inicia automáticamente ambos servidores en segundo plano.

## 📚 Flujo de Uso

1. **Abrir la aplicación** en `http://localhost:5173`

2. **Página de Inicio:**
   - Subir los 4 archivos CSV requeridos:
     - `posiciones.csv`
     - `instruments.csv`
     - `allocations_nuevas.csv`
     - `allocations_currency.csv` (allocations antiguas)
   - Click en "Procesar" para ejecutar el pipeline

3. **Durante el procesamiento:**
   - Verás una barra de progreso en tiempo real
   - El sistema ejecuta el pipeline completo automáticamente

4. **Página de Validación:**
   - Una vez completado, navega a "Validación"
   - Verás la tabla con todos los instrumentos procesados
   - Filtros por estado: Balanceado, No Balanceado, Sin datos
   - Búsqueda por instrumento, ID o moneda

5. **Página de Visualización:**
   - Gráficos interactivos con los resultados
   - Distribución por estado, moneda, región, etc.

## 🔌 API Endpoints

| Método | Endpoint | Descripción |
|--------|----------|-------------|
| GET | `/api/health` | Health check |
| POST | `/api/upload` | Subir archivos CSV |
| POST | `/api/process` | Ejecutar pipeline |
| GET | `/api/status` | Estado del procesamiento |
| GET | `/api/results/validation` | Obtener datos procesados |
| GET | `/api/results/exports/<tipo>` | Obtener export específico |
| GET | `/api/download/<tipo>` | Descargar CSV |
| DELETE | `/api/reset` | Reiniciar estado |

## 📁 Estructura del Proyecto

```
allocations_validation/
├── api/                          # Backend Flask
│   ├── app.py                    # API principal
│   ├── requirements.txt
│   └── README.md
├── dashboard-financiero/         # Frontend React
│   ├── src/
│   │   ├── components/           # Componentes UI
│   │   ├── pages/                # Páginas
│   │   ├── services/             # API service
│   │   └── context/              # Estado global
│   └── package.json
├── data/
│   ├── raw/                      # Archivos subidos
│   ├── processed/                # Resultados procesados
│   └── exports/                  # CSVs generados
├── src/                          # Lógica del pipeline
│   ├── extractors/               # Carga de datos
│   ├── logic/                    # Procesamiento
│   └── utils/
└── run_pipeline.py               # Pipeline standalone
```

## 🔧 Desarrollo

### Backend

El backend utiliza Flask con threading para procesamiento asíncrono:
- Los archivos se guardan en `data/raw/`
- El pipeline se ejecuta en background
- Los resultados se guardan en `data/processed/` y `data/exports/`

### Frontend

El frontend utiliza React + Vite:
- Estado global con Context API
- Polling para verificar progreso del procesamiento
- Actualización automática de datos

## 🐛 Solución de Problemas

### "Error al conectar con la API"
- Verifica que el backend esté corriendo en el puerto 5000
- Revisa la consola del backend para errores

### "No hay datos procesados"
- Asegúrate de haber subido y procesado archivos primero
- Ve a la página de Inicio y sube los archivos

### "Los archivos no se procesan"
- Verifica que los archivos tengan los nombres correctos
- Verifica que sean archivos CSV válidos
- Revisa los logs del backend en la terminal

## 📝 Notas

- Los archivos deben estar en formato CSV
- Tamaño máximo por archivo: 50MB
- El procesamiento puede tardar varios minutos dependiendo del tamaño
- Los datos procesados se mantienen hasta reiniciar el servidor

## 🤝 Soporte

Para reportar problemas o sugerencias, contacta al equipo de desarrollo.
